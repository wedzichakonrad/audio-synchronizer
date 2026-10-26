import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from audio_sync.actions import copy_files, delete_files
from audio_sync.adb import Adb, AdbError
from audio_sync.comparison import compare
from audio_sync.storage import LocalStorage, PhoneStorage
from ui.background import run_in_background
from ui.path_row import PathRow
from ui.phone_browser import PhoneBrowser
from ui.results_view import ResultsView

MODE_PHONE = "phone"
MODE_PC = "pc"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Synchronizer")
        self.geometry("760x620")
        self.minsize(620, 540)

        self.mode = tk.StringVar(value=MODE_PHONE)
        self.plan = None    # ostatni wynik porównania
        self.source = None  # Storage źródła z ostatniego porównania
        self.target = None  # Storage celu z ostatniego porównania
        self.note = ""      # krótkie podsumowanie akcji, pokazywane po odświeżeniu

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(7, weight=1)  # wyniki zabierają całe wolne miejsce

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

        # wyniki: listy z polami wyboru
        self.results_view = ResultsView(frame, self.on_copy, self.on_delete)
        self.results_view.grid(row=7, column=0, sticky="nsew", pady=(12, 0))

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

        self.source = LocalStorage(source_path)
        self.target = self.build_target(target_path)
        self.note = ""
        self.run_compare()

    def run_compare(self):
        """Porównuje self.source z self.target (też do odświeżania po akcjach)."""
        source, target = self.source, self.target
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
        self.results_view.show(plan)
        self.status.set(
            f"{self.note}Źródło: {plan.source_count}, cel: {plan.target_count} | "
            f"do skopiowania: {len(plan.to_copy)}, nadmiarowe: {len(plan.extra)}"
        )
        self.note = ""

    def on_compare_error(self, error):
        self.set_busy(False, "Błąd.")
        messagebox.showerror("Błąd porównania", str(error))

    # --- akcje: kopiowanie i usuwanie ---

    def on_copy(self, paths):
        if not paths:
            messagebox.showinfo("Nic nie zaznaczono", "Zaznacz pliki do skopiowania.")
            return
        source, target = self.source, self.target
        self.run_action(
            "Kopiuję",
            work=lambda report: copy_files(source, target, paths, report),
            done_label="Skopiowano",
        )

    def on_delete(self, paths):
        if not paths:
            messagebox.showinfo("Nic nie zaznaczono", "Zaznacz pliki do usunięcia.")
            return
        confirmed = messagebox.askyesno(
            "Potwierdź usunięcie",
            f"Usunąć {len(paths)} plików z folderu docelowego?\n\n"
            "Tej operacji nie można cofnąć (pliki nie trafią do kosza).",
            icon="warning",
            default="no",
        )
        if not confirmed:
            return
        target = self.target
        self.run_action(
            "Usuwam",
            work=lambda report: delete_files(target, paths, report),
            done_label="Usunięto",
        )

    def run_action(self, verb, work, done_label):
        self.set_busy(True, f"{verb}...", determinate=True)
        run_in_background(
            self,
            work=work,
            on_success=lambda result: self.on_action_done(result, done_label),
            on_error=self.on_compare_error,
            on_progress=lambda info: self.on_action_progress(verb, info),
        )

    def on_action_progress(self, verb, info):
        done, total, rel = info
        self.progress.config(maximum=total, value=done)
        self.status.set(f"{verb} {done}/{total}: {rel}")

    def on_action_done(self, result, done_label):
        self.set_busy(False)
        self.note = f"{done_label}: {result.done} | "
        if result.errors:
            shown = "\n".join(f"{rel}: {msg}" for rel, msg in result.errors[:10])
            more = len(result.errors) - 10
            if more > 0:
                shown += f"\n... i {more} więcej"
            messagebox.showwarning(
                "Część operacji się nie powiodła",
                f"Błędy: {len(result.errors)}\n\n{shown}",
            )
        self.run_compare()  # odśwież listy, żeby pokazywały stan po akcji

    # --- pasek postępu i blokada przycisków ---

    def set_busy(self, busy, message=None, determinate=False):
        if busy:
            self.compare_button.state(["disabled"])  # blokada przed podwójnym kliknięciem
            self.results_view.set_enabled(False)
            if determinate:
                self.progress.config(mode="determinate", value=0)
            else:
                self.progress.config(mode="indeterminate")
                self.progress.start(15)
        else:
            self.progress.stop()
            self.progress.config(mode="indeterminate", value=0)
            self.compare_button.state(["!disabled"])
            self.results_view.set_enabled(True)
        if message:
            self.status.set(message)