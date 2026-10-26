from tkinter import ttk

from ui.check_list import CheckList


class ResultsView(ttk.Frame):
    """Dwie zakładki: pliki do skopiowania i pliki nadmiarowe."""

    def __init__(self, parent, on_copy, on_delete):
        super().__init__(parent)
        self._buttons = []

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        copy_tab, self.copy_list = self._build_tab(
            checked_by_default=True, action_text="Skopiuj zaznaczone", action=on_copy
        )
        extra_tab, self.extra_list = self._build_tab(
            checked_by_default=False, action_text="Usuń zaznaczone", action=on_delete
        )
        self.notebook.add(copy_tab, text="Do skopiowania (0)")
        self.notebook.add(extra_tab, text="Nadmiarowe (0)")

    def _build_tab(self, checked_by_default, action_text, action):
        tab = ttk.Frame(self.notebook, padding=8)
        check_list = CheckList(tab, checked_by_default)
        check_list.pack(fill="both", expand=True)

        bar = ttk.Frame(tab)
        bar.pack(fill="x", pady=(8, 0))
        select_all = ttk.Button(
            bar, text="Zaznacz wszystko", command=lambda: check_list.set_all(True)
        )
        select_none = ttk.Button(
            bar, text="Odznacz wszystko", command=lambda: check_list.set_all(False)
        )
        do_action = ttk.Button(
            bar, text=action_text, command=lambda: action(check_list.checked_paths())
        )
        select_all.pack(side="left")
        select_none.pack(side="left", padx=8)
        do_action.pack(side="right")

        self._buttons += [select_all, select_none, do_action]
        return tab, check_list

    def show(self, plan):
        self.copy_list.load(plan.to_copy)
        self.extra_list.load(plan.extra)
        self.notebook.tab(0, text=f"Do skopiowania ({len(plan.to_copy)})")
        self.notebook.tab(1, text=f"Nadmiarowe ({len(plan.extra)})")

    def set_enabled(self, enabled):
        state = ["!disabled"] if enabled else ["disabled"]
        for button in self._buttons:
            button.state(state)