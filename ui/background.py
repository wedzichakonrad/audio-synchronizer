import queue
import threading


def run_in_background(widget, work, on_success, on_error, on_progress=None):
    """Uruchamia work w osobnym wątku, a wyniki przekazuje do głównego wątku okna.

    Bez on_progress: work() nie dostaje argumentów.
    Z on_progress: work(report) dostaje funkcję report(...), którą może wołać
    w trakcie pracy; on_progress dostaje krotkę z jej argumentami.
    on_success, on_error i on_progress wywołują się w wątku okna,
    więc wolno w nich bezpiecznie ruszać widżety.
    """
    results = queue.Queue()

    def worker():
        try:
            if on_progress is None:
                result = work()
            else:
                result = work(lambda *info: results.put(("progress", info)))
            results.put(("ok", result))
        except Exception as e:  # wyjątek w wątku inaczej zniknąłby po cichu
            results.put(("error", e))

    def poll():
        try:
            while True:  # opróżnij wszystko, co się zebrało od ostatniego razu
                kind, payload = results.get_nowait()
                if kind == "progress":
                    on_progress(payload)
                elif kind == "ok":
                    on_success(payload)
                    return
                else:
                    on_error(payload)
                    return
        except queue.Empty:
            widget.after(100, poll)

    threading.Thread(target=worker, daemon=True).start()
    widget.after(100, poll)