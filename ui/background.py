import queue
import threading


def run_in_background(widget, work, on_success, on_error):
    """Uruchamia work() w osobnym wątku, a wynik przekazuje do głównego wątku okna.

    on_success(wynik) i on_error(wyjatek) wywołają się już w wątku okna,
    więc wolno w nich bezpiecznie ruszać widżety.
    """
    results = queue.Queue()

    def worker():
        try:
            results.put(("ok", work()))
        except Exception as e:  # wyjątek w wątku inaczej zniknąłby po cichu
            results.put(("error", e))

    def poll():
        try:
            kind, payload = results.get_nowait()
        except queue.Empty:
            widget.after(100, poll)
            return
        if kind == "ok":
            on_success(payload)
        else:
            on_error(payload)

    threading.Thread(target=worker, daemon=True).start()
    widget.after(100, poll)