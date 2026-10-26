import shlex
import subprocess


class AdbError(Exception):
    """Błąd przy komunikacji z telefonem przez ADB."""


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
            raise AdbError(f"ADB not found at: {self.adb_path}")
        if proc.returncode != 0:
            raise AdbError(proc.stderr.strip() or proc.stdout.strip() or "Unknown ADB error")
        return proc.stdout

    def shell(self, command):
        return self.run("shell", command)

    def push(self, local_path, remote_path):
        self.run("push", str(local_path), remote_path)

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
                result.append(("Internal Storage", "/storage/emulated/0"))
            else:
                result.append((f"SD Card ({name})", f"/storage/{name}"))
        return result

    def list_dirs(self, path):
        """Zwraca posortowane nazwy podfolderów w danym folderze telefonu."""
        out = self.shell(f"ls -1 -p {shlex.quote(path)}")
        dirs = [line[:-1] for line in out.splitlines() if line.endswith("/")]
        return sorted(dirs, key=str.lower)