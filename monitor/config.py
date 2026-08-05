from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo


TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")


@dataclass(frozen=True)
class EditorialConfig:
    summary_hours: int = 4
    degraded_threshold: float = 0.60
    max_summary_topics: int = 40
    gnews_is_date_certifying: bool = False
    ai_enabled_by_default: bool = False

