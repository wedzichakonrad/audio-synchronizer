import tkinter as tk
from tkinter import messagebox, ttk

from audio_sync.adb import Adb, AdbError


class PhoneBrowser(tk.Toplevel):
    """Okienko do wyboru folderu na telefonie. Wynik ląduje w self.result."""

    def __init__(self, parent, adb: Adb):
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