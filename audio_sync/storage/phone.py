import shlex

from audio_sync.adb import Adb
from audio_sync.filters import is_audio_file, normalize


class PhoneStorage:
    def __init__(self, adb: Adb, root: str):
        self.adb = adb
        self.root = root.rstrip("/")

    def _remote(self, rel_path):
        return self.root + "/" + rel_path

    def list_files(self):
        out = self.adb.shell(f"find {shlex.quote(self.root)} -type f")
        prefix = self.root + "/"
        result = set()
        for line in out.splitlines():
            if line.startswith(prefix) and is_audio_file(line):
                result.add(normalize(line[len(prefix):]))
        return result

    def put(self, local_file, rel_path):
        remote = self._remote(rel_path)
        remote_dir = remote.rsplit("/", 1)[0]
        self.adb.shell(f"mkdir -p {shlex.quote(remote_dir)}")  # np. nowy album
        self.adb.push(local_file, remote)

    def delete(self, rel_path):
        self.adb.shell(f"rm {shlex.quote(self._remote(rel_path))}")