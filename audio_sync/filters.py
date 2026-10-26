import unicodedata
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".mp4"}


def normalize(path):
    """Ujednolica zapis polskich znaków (np. "ą" zapisane na dwa sposoby)."""
    return unicodedata.normalize("NFC", path)


def is_audio_file(path):
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS