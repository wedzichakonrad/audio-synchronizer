import tkinter as tk
from tkinter import ttk


class PathRow(ttk.Frame):
    """Wiersz: opis, pole tekstowe i przycisk "Wybierz..."."""

    def __init__(self, parent, label, on_browse, initial=""):
        super().__init__(parent)
        self._var = tk.StringVar(value=initial)

        self._label = ttk.Label(self, text=label, width=22)
        self._label.pack(side="left")
        ttk.Entry(self, textvariable=self._var).pack(
            side="left", fill="x", expand=True, padx=8
        )
        ttk.Button(self, text="Wybierz...", command=on_browse).pack(side="left")

    def get(self):
        return self._var.get().strip()

    def set(self, value):
        self._var.set(value)

    def set_label(self, text):
        self._label.config(text=text)