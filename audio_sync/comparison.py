from audio_sync.models import Plan
from audio_sync.storage import Storage


def compare(source: Storage, target: Storage) -> Plan:
    source_files = source.list_files()
    target_files = target.list_files()
    return Plan(
        to_copy=sorted(source_files - target_files),
        extra=sorted(target_files - source_files),
        source_count=len(source_files),
        target_count=len(target_files),
    )