from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .config import TZ_AR


def parse_datetime(value: object, tz: ZoneInfo = TZ_AR) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def in_window(value: datetime | None, now: datetime, hours: int) -> bool:
    if value is None:
        return False
    current = parse_datetime(now)
    moment = parse_datetime(value)
    return bool(current and moment and current.timestamp() - hours * 3600 <= moment.timestamp() <= current.timestamp())

