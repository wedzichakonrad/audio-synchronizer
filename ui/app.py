import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from audio_sync.adb import Adb, AdbError
from audio_sync.comparison import compare
from audio_sync.storage import LocalStorage, PhoneStorage
from ui.background import run_in_background
from ui.path_row import PathRow
from ui.phone_browser import PhoneBrowser

MODE_PHONE = "phone"
MODE_PC = "pc"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Synchronizer")
        self.geometry("700x320")
        self.minsize(500, 300)

        self.mode = tk.StringVar(value=MODE_PHONE)
        self.plan = None  # ostatni wynik porównania, przyda się w następnym etapie

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        # wybór trybu
        mode_bar = ttk.Frame(frame)
        mode_bar.grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(mode_bar, text="Tryb:").pack(side="left", padx=(0, 8))
        ttk.Radiobutton(
            mode_bar, text="Komputer → telefon", value=MODE_PHONE,
            variable=self.mode, command=self.on_mode_change,
        ).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(
            mode_bar, text="Dwa foldery na komputerze", value=MODE_PC,
            variable=self.mode, command=self.on_mode_change,
        ).pack(side="left")

        # wiersze ze ścieżkami
        self.adb_row = PathRow(frame, "ADB:", self.choose_adb, initial="adb")
        self.source_row = PathRow(frame, "", self.choose_source)
        self.target_row = PathRow(frame, "", self.choose_target)
        self.adb_row.grid(row=1, column=0, sticky="ew", pady=4)
        self.source_row.grid(row=2, column=0, sticky="ew", pady=4)
        self.target_row.grid(row=3, column=0, sticky="ew", pady=4)

        # przycisk, pasek postępu, status
        self.compare_button = ttk.Button(frame, text="Porównaj", command=self.on_compare)
        self.compare_button.grid(row=4, column=0, pady=(16, 0))
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        self.status = tk.StringVar(value="Gotowy.")
        ttk.Label(frame, textvariable=self.status).grid(
            row=6, column=0, sticky="w", pady=(8, 0)
        )

        self.apply_mode()

    # --- tryb ---

    def on_mode_change(self):
        self.target_row.set("")  # stara ścieżka (np. z telefonu) nie pasuje do nowego trybu
        self.apply_mode()

    def apply_mode(self):
        if self.mode.get() == MODE_PHONE:
            self.adb_row.grid()  # przywraca wiersz na swoje miejsce
            self.source_row.set_label("Folder na komputerze:")
            self.target_row.set_label("Folder na telefonie:")
        else:
            self.adb_row.grid_remove()  # chowa wiersz, pamiętając jego położenie
            self.source_row.set_label("Folder źródłowy:")
            self.target_row.set_label("Folder do porównania:")

    # --- wybór ścieżek ---

    def choose_adb(self):
        path = filedialog.askopenfilename(
            title="Wskaż adb.exe",
            filetypes=[("adb", "adb.exe"), ("Wszystkie pliki", "*.*")],
        )
        if path:  # przy kliknięciu "Anuluj" dostajemy pusty tekst
            self.adb_row.set(path)

    def choose_source(self):
        path = filedialog.askdirectory(title="Wybierz folder źródłowy na komputerze")
        if path:
            self.source_row.set(path)

    def choose_target(self):
        if self.mode.get() == MODE_PHONE:
            self.choose_phone_folder()
        else:
            path = filedialog.askdirectory(title="Wybierz drugi folder na komputerze")
            if path:
                self.target_row.set(path)

    def choose_phone_folder(self):
        adb = Adb(self.adb_row.get())
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
            self.target_row.set(dialog.result)

    # --- porównanie ---

    def build_target(self, target_path):
        """Fabryka: z trybu i ścieżki robi odpowiedni obiekt Storage."""
        if self.mode.get() == MODE_PHONE:
            return PhoneStorage(Adb(self.adb_row.get()), target_path)
        return LocalStorage(target_path)

    def on_compare(self):
        source_path = self.source_row.get()
        target_path = self.target_row.get()
        pc_mode = self.mode.get() == MODE_PC

        if not source_path or not target_path:
            messagebox.showwarning("Brak ścieżek", "Wybierz oba foldery.")
            return
        if not Path(source_path).is_dir():
            messagebox.showerror("Błąd", f"Folder nie istnieje:\n{source_path}")
            return
        if pc_mode and not Path(target_path).is_dir():
            messagebox.showerror("Błąd", f"Folder nie istnieje:\n{target_path}")
            return
        if pc_mode and Path(source_path).resolve() == Path(target_path).resolve():
            messagebox.showwarning("Te same foldery", "Wybrano dwa razy ten sam folder.")
            return

        source = LocalStorage(source_path)
        target = self.build_target(target_path)

        self.set_busy(True, "Porównuję pliki...")
        run_in_background(
            self,
            work=lambda: compare(source, target),
            on_success=self.on_compare_done,
            on_error=self.on_compare_error,
        )

    def on_compare_done(self, plan):
        self.set_busy(False)
        self.plan = plan
        self.status.set(
            f"Źródło: {plan.source_count}, cel: {plan.target_count} | "
            f"do skopiowania: {len(plan.to_copy)}, nadmiarowe: {len(plan.extra)}"
        )

    def on_compare_error(self, error):
        self.set_busy(False, "Błąd.")
        messagebox.showerror("Błąd porównania", str(error))

    def set_busy(self, busy, message=None):
        if busy:
            self.compare_button.state(["disabled"])  # blokada przed podwójnym kliknięciem
            self.progress.start(15)
        else:
            self.compare_button.state(["!disabled"])
            self.progress.stop()
        if message:
            self.status.set(message)