from dataclasses import dataclass

@dataclass
class Plan:
    to_copy: list      # względne ścieżki: są w źródle, brak w celu
    extra: list        # względne ścieżki: są w celu, brak w źródle
    source_count: int
    target_count: int