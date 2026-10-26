import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core import Adb, AdbError, compare_local, compare_with_phone

MODE_PHONE = "phone"
MODE_PC = "pc"


class PhoneBrowser(tk.Toplevel):
    """Okienko do wyboru folderu na telefonie. Wynik ląduje w self.result."""

    def __init__(self, parent, adb):
        super().__init__(parent)
        self.title("Wybierz folder na telefonie")
        self.geometry("480x420")
        self.transient(parent)  # okno "należy" do głównego
        self.grab_set()         # blokuje główne okno, dopóki to nie zostanie zamknięte

        self.adb = adb
        self.result = None
        self.current = None     # None = ekran wyboru pamięci
        self.entries = []
        self.storages = adb.list_storages()
        self.storage_roots = {path for _, path in self.storages}

        self.path_label = ttk.Label(self, anchor="w")
        self.path_label.pack(fill="x", padx=10, pady=(10, 4))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10)
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, activestyle="none"
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<Double-Button-1>", self.on_open)
        self.listbox.bind("<Return>", self.on_open)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=10, pady=10)
        self.up_button = ttk.Button(buttons, text="W górę", command=self.go_up)
        self.up_button.pack(side="left")
        ttk.Button(buttons, text="Anuluj", command=self.destroy).pack(side="right")
        self.select_button = ttk.Button(
            buttons, text="Wybierz ten folder", command=self.on_select
        )
        self.select_button.pack(side="right", padx=(0, 8))

        self.show(None)

    def show(self, path):
        """Pokazuje zawartość folderu (albo listę pamięci, gdy path to None)."""
        try:
            if path is None:
                names = [name for name, _ in self.storages]
            else:
                names = self.adb.list_dirs(path)
        except AdbError as e:
            messagebox.showerror("Błąd ADB", str(e), parent=self)
            return

        self.current = path
        self.entries = names
        self.listbox.delete(0, "end")
        for name in names:
            self.listbox.insert("end", name)
        self.path_label.config(text=path or "Wybierz pamięć telefonu")

        state = ["disabled"] if path is None else ["!disabled"]
        self.up_button.state(state)
        self.select_button.state(state)

    def on_open(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if self.current is None:
            path = self.storages[index][1]
        else:
            path = self.current + "/" + self.entries[index]
        self.show(path)

    def go_up(self):
        if self.current in self.storage_roots:
            self.show(None)
        else:
            self.show(self.current.rsplit("/", 1)[0])

    def on_select(self):
        self.result = self.current
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Synchronizer")
        self.geometry("700x320")
        self.minsize(500, 300)

        # zmienne "połączone" z polami tekstowymi
        self.mode = tk.StringVar(value=MODE_PHONE)
        self.adb_path = tk.StringVar(value="adb")
        self.source_root = tk.StringVar()
        self.target_root = tk.StringVar()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)  # kolumna z polami tekstowymi się rozciąga

        # wiersz 0: wybór trybu
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(mode_frame, text="Tryb:").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(
            mode_frame, text="Komputer → telefon", value=MODE_PHONE,
            variable=self.mode, command=self.on_mode_change,
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            mode_frame, text="Dwa foldery na komputerze", value=MODE_PC,
            variable=self.mode, command=self.on_mode_change,
        ).pack(side="left")

        # wiersz 1: ADB (widoczny tylko w trybie telefonu)
        self.adb_widgets = self.add_row(
            frame, 1, "ADB:", self.adb_path, "Wybierz...", self.choose_adb
        )
        # wiersze 2 i 3: źródło i cel (opisy zmieniają się zależnie od trybu)
        self.source_label, _, _ = self.add_row(
            frame, 2, "", self.source_root, "Wybierz...", self.choose_source
        )
        self.target_label, _, _ = self.add_row(
            frame, 3, "", self.target_root, "Wybierz...", self.choose_target
        )

        self.compare_button = ttk.Button(frame, text="Porównaj", command=self.on_compare)
        self.compare_button.grid(row=4, column=0, columnspan=3, pady=(16, 0))

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        self.status = tk.StringVar(value="Gotowy.")
        ttk.Label(frame, textvariable=self.status).grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        self.results = queue.Queue()  # tędy wątek roboczy przekazuje wynik do okna
        self.plan = None              # ostatni wynik porównania, przyda się w etapie 5

        self.apply_mode()

    def add_row(self, parent, row, label, variable, button_text, command):
        """Tworzy wiersz: opis, pole tekstowe, przycisk. Zwraca te trzy widżety."""
        label_widget = ttk.Label(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", padx=8)
        button = ttk.Button(parent, text=button_text, command=command)
        button.grid(row=row, column=2)
        return label_widget, entry, button

    # --- tryb ---

    def on_mode_change(self):
        self.target_root.set("")  # stara ścieżka (np. z telefonu) nie pasuje do nowego trybu
        self.apply_mode()

    def apply_mode(self):
        if self.mode.get() == MODE_PHONE:
            for widget in self.adb_widgets:
                widget.grid()  # przywraca widżet z poprzednim położeniem
            self.source_label.config(text="Folder na komputerze:")
            self.target_label.config(text="Folder na telefonie:")
        else:
            for widget in self.adb_widgets:
                widget.grid_remove()  # chowa widżet, ale pamięta jego położenie
            self.source_label.config(text="Folder źródłowy:")
            self.target_label.config(text="Folder do porównania:")

    # --- wybór ścieżek ---

    def choose_adb(self):
        path = filedialog.askopenfilename(
            title="Wskaż adb.exe",
            filetypes=[("adb", "adb.exe"), ("Wszystkie pliki", "*.*")],
        )
        if path:  # przy kliknięciu "Anuluj" dostajemy pusty tekst
            self.adb_path.set(path)

    def choose_source(self):
        path = filedialog.askdirectory(title="Wybierz folder źródłowy na komputerze")
        if path:
            self.source_root.set(path)

    def choose_target(self):
        if self.mode.get() == MODE_PHONE:
            self.choose_phone_folder()
        else:
            path = filedialog.askdirectory(title="Wybierz drugi folder na komputerze")
            if path:
                self.target_root.set(path)

    def choose_phone_folder(self):
        adb = Adb(self.adb_path.get())
        try:
            devices = adb.devices()
        except AdbError as e:
            messagebox.showerror("Błąd ADB", str(e))
            return
        if not any(status == "device" for _, status in devices):
            messagebox.showwarning(
                "Brak telefonu",
                "Nie wykryto autoryzowanego telefonu.\n"
                "Podłącz go, odblokuj i zaakceptuj debugowanie USB.",
            )
            return

        dialog = PhoneBrowser(self, adb)
        self.wait_window(dialog)  # czeka, aż okienko zostanie zamknięte
        if dialog.result:
            self.target_root.set(dialog.result)

    # --- porównanie ---

    def on_compare(self):
        mode = self.mode.get()
        source = self.source_root.get().strip()
        target = self.target_root.get().strip()
        if not source or not target:
            messagebox.showwarning("Brak ścieżek", "Wybierz oba foldery.")
            return
        if not Path(source).is_dir():
            messagebox.showerror("Błąd", f"Folder nie istnieje:\n{source}")
            return
        if mode == MODE_PC and not Path(target).is_dir():
            messagebox.showerror("Błąd", f"Folder nie istnieje:\n{target}")
            return
        if mode == MODE_PC and Path(source).resolve() == Path(target).resolve():
            messagebox.showwarning("Te same foldery", "Wybrano dwa razy ten sam folder.")
            return

        self.compare_button.state(["disabled"])  # blokada przed podwójnym kliknięciem
        self.status.set("Porównuję pliki...")
        self.progress.start(15)

        adb = Adb(self.adb_path.get()) if mode == MODE_PHONE else None
        threading.Thread(
            target=self.compare_worker, args=(mode, adb, source, target), daemon=True
        ).start()
        self.after(100, self.check_results)

    def compare_worker(self, mode, adb, source, target):
        # to działa w osobnym wątku: NIE wolno tu dotykać widżetów
        try:
            if mode == MODE_PHONE:
                plan = compare_with_phone(adb, source, target)
            else:
                plan = compare_local(source, target)
            self.results.put(("ok", plan))
        except Exception as e:
            self.results.put(("error", str(e)))

    def check_results(self):
        # to działa w głównym wątku, co 100 ms zagląda do kolejki
        try:
            kind, payload = self.results.get_nowait()
        except queue.Empty:
            self.after(100, self.check_results)
            return

        self.progress.stop()
        self.compare_button.state(["!disabled"])
        if kind == "error":
            self.status.set("Błąd.")
            messagebox.showerror("Błąd porównania", payload)
            return

        self.plan = payload
        self.status.set(
            f"Źródło: {payload.source_count}, cel: {payload.target_count} | "
            f"do skopiowania: {len(payload.to_copy)}, nadmiarowe: {len(payload.extra)}"
        )


if __name__ == "__main__":
    App().mainloop()