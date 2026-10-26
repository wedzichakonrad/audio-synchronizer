from dataclasses import dataclass

from audio_sync.adb import AdbError
from audio_sync.storage import LocalStorage, Storage


@dataclass
class ActionResult:
    done: int
    errors: list  # pary (ścieżka względna, komunikat błędu)


def copy_files(source: LocalStorage, target: Storage, rel_paths, progress=None):
    """Kopiuje wskazane pliki ze źródła do celu."""
    return _run(rel_paths, lambda rel: target.put(source.path_of(rel), rel), progress)


def delete_files(target: Storage, rel_paths, progress=None):
    """Usuwa wskazane pliki z celu."""
    return _run(rel_paths, target.delete, progress)


def _run(rel_paths, operation, progress):
    errors = []
    total = len(rel_paths)
    for index, rel in enumerate(rel_paths, 1):
        try:
            operation(rel)
        except (AdbError, OSError) as e:
            errors.append((rel, str(e)))  # jeden zły plik nie zatrzymuje reszty
        if progress:
            progress(index, total, rel)
    return ActionResult(done=total - len(errors), errors=errors)