import shutil
from pathlib import Path

from audio_sync.filters import is_audio_file, normalize


class LocalStorage:
    def __init__(self, root):
        self.root = Path(root)

    def path_of(self, rel_path):
        """Pełna ścieżka pliku na dysku (potrzebna np. do kopiowania z tego miejsca)."""
        return self.root / rel_path

    def list_files(self):
        result = set()
        for p in self.root.rglob("*"):
            if p.is_file() and is_audio_file(p.name):
                result.add(normalize(p.relative_to(self.root).as_posix()))
        return result

    def put(self, local_file, rel_path):
        destination = self.path_of(rel_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_file, destination)

    def delete(self, rel_path):
        self.path_of(rel_path).unlink()