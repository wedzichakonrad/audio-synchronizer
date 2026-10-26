from tkinter import ttk

CHECKED = "☑"
UNCHECKED = "☐"


class CheckList(ttk.Frame):
    """Lista ścieżek z polami wyboru (klik w kolumnę ☐/☑ albo spacja)."""

    def __init__(self, parent, checked_by_default):
        super().__init__(parent)
        self.checked_by_default = checked_by_default
        self.paths = {}      # id wiersza -> ścieżka względna
        self.checked = set() # id zaznaczonych wierszy

        self.tree = ttk.Treeview(
            self, columns=("mark", "path"), show="headings", selectmode="browse"
        )
        self.tree.heading("mark", text="")
        self.tree.heading("path", text="Plik")
        self.tree.column("mark", width=40, stretch=False, anchor="center")
        self.tree.column("path", anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<space>", self.on_space)

    def _mark(self, iid):
        return CHECKED if iid in self.checked else UNCHECKED

    def load(self, paths):
        """Wypełnia listę nowymi ścieżkami (zastępuje poprzednie)."""
        self.tree.delete(*self.tree.get_children())
        self.paths = {}
        self.checked = set()
        for index, path in enumerate(paths):
            iid = str(index)
            self.paths[iid] = path
            if self.checked_by_default:
                self.checked.add(iid)
            self.tree.insert("", "end", iid=iid, values=(self._mark(iid), path))

    def toggle(self, iid):
        if iid in self.checked:
            self.checked.discard(iid)
        else:
            self.checked.add(iid)
        self.tree.set(iid, "mark", self._mark(iid))

    def set_all(self, value):
        self.checked = set(self.paths) if value else set()
        for iid in self.paths:
            self.tree.set(iid, "mark", self._mark(iid))

    def checked_paths(self):
        """Zaznaczone ścieżki w tej samej kolejności, w jakiej leżą na liście."""
        return [self.paths[iid] for iid in sorted(self.checked, key=int)]

    def on_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":  # tylko kolumna z polem wyboru
            return
        iid = self.tree.identify_row(event.y)
        if iid:
            self.toggle(iid)
            return "break"  # nie zmieniaj zaznaczenia wiersza przy okazji

    def on_space(self, event):
        for iid in self.tree.selection():
            self.toggle(iid)
        return "break"