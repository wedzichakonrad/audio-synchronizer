import shlex
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

EXTENSIONS = {".mp3", ".m4a", ".mp4"}


class AdbError(Exception):
    """Błąd przy komunikacji z telefonem przez ADB."""


def normalize(path):
    return unicodedata.normalize("NFC", path)


def has_audio_extension(path):
    return Path(path).suffix.lower() in EXTENSIONS


@dataclass
class Plan:
    to_copy: list      # względne ścieżki: są na komputerze, brak na telefonie
    extra: list        # względne ścieżki: są na telefonie, brak na komputerze
    local_count: int
    phone_count: int


class Adb:
    def __init__(self, adb_path="adb"):
        self.adb_path = adb_path

    def run(self, *args):
        try:
            proc = subprocess.run(
                [self.adb_path, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,  # bez migającego okna konsoli
            )
        except FileNotFoundError:
            raise AdbError(f"Nie znaleziono ADB pod ścieżką: {self.adb_path}")
        if proc.returncode != 0:
            raise AdbError(proc.stderr.strip() or proc.stdout.strip() or "Nieznany błąd ADB")
        return proc.stdout

    def shell(self, command):
        return self.run("shell", command)

    def devices(self):
        """Zwraca listę (numer_seryjny, status), np. ('R58...', 'device')."""
        lines = self.run("devices").splitlines()[1:]
        result = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                result.append((parts[0], parts[1]))
        return result

    def list_storages(self):
        """Zwraca listę (nazwa, ścieżka): pamięć wewnętrzna i karty SD."""
        result = []
        for name in self.shell("ls /storage").split():
            if name == "self":
                continue
            if name == "emulated":
                result.append(("Pamięć wewnętrzna", "/storage/emulated/0"))
            else:
                result.append((f"Karta SD ({name})", f"/storage/{name}"))
        return result

    def list_dirs(self, path):
        """Zwraca posortowane nazwy podfolderów w danym folderze telefonu."""
        out = self.shell(f"ls -1 -p {shlex.quote(path)}")
        dirs = [line[:-1] for line in out.splitlines() if line.endswith("/")]
        return sorted(dirs, key=str.lower)

    def list_files(self, root):
        out = self.shell(f"find {shlex.quote(root)} -type f")
        prefix = root.rstrip("/") + "/"
        result = set()
        for line in out.splitlines():
            if line.startswith(prefix) and has_audio_extension(line):
                result.add(normalize(line[len(prefix):]))
        return result

    def push(self, local_root, phone_root, rel_path):
        local_path = str(Path(local_root) / rel_path)
        remote_path = phone_root.rstrip("/") + "/" + rel_path
        remote_dir = remote_path.rsplit("/", 1)[0]
        self.shell(f"mkdir -p {shlex.quote(remote_dir)}")
        self.run("push", local_path, remote_path)

    def delete(self, phone_root, rel_path):
        remote_path = phone_root.rstrip("/") + "/" + rel_path
        self.shell(f"rm {shlex.quote(remote_path)}")


def list_local(root):
    root = Path(root)
    result = set()
    for p in root.rglob("*"):
        if p.is_file() and has_audio_extension(p.name):
            result.add(normalize(p.relative_to(root).as_posix()))
    return result


def compare(adb, local_root, phone_root):
    local = list_local(local_root)
    phone = adb.list_files(phone_root)
    return Plan(
        to_copy=sorted(local - phone),
        extra=sorted(phone - local),
        local_count=len(local),
        phone_count=len(phone),
    )