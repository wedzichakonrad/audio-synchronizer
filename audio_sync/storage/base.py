from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    """Miejsce, w którym leżą pliki (folder na dysku, telefon...)."""

    def list_files(self) -> set[str]:
        """Zwraca zbiór ścieżek względnych plików audio."""
        ...

    def put(self, local_file: Path, rel_path: str) -> None:
        """Kopiuje plik z dysku komputera do tego miejsca."""
        ...

    def delete(self, rel_path: str) -> None:
        """Usuwa plik z tego miejsca."""
        ...