from __future__ import annotations

import hashlib
import html
import os
import re
import unicodedata
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from zoneinfo import ZoneInfo

TZ_AR = ZoneInfo("America/Argentina/Buenos_Aires")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "si", "sí", "on", "full"}


def env_int(name: str, default: int, minimum: int | None = None,
            maximum: int | None = None) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def now_ar() -> datetime:
    return datetime.now(TZ_AR)


def normalize_text(text: str) -> str:
    raw = unicodedata.normalize("NFD", (text or "").lower())
    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", raw).strip()


def stable_id(text: str, prefix: str = "a") -> str:
    digest = hashlib.sha1((text or "").encode("utf-8", errors="ignore")).hexdigest()[:14]
    return f"{prefix}_{digest}"


def canonical_cluster_id(title: str) -> str:
    """Devuelve el mismo identificador de historia en todas las capas.

    La persistencia histórica usa ``monitor_core.normalizar_titulo``. Reutilizar
    exactamente esa normalización evita que Temas, Recomendaciones, Cambios y
    la mesa editorial generen cuatro IDs diferentes para el mismo título.
    """
    try:
        from monitor_core import normalizar_titulo
        base = " ".join(sorted(normalizar_titulo(title))) or normalize_text(title) or str(title or "")
    except Exception:
        base = " ".join(sorted(normalize_text(title).split())) or str(title or "")
    return stable_id(base, "c")


def clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(max(low, min(high, round(value))))


def safe_html(text: Any) -> str:
    return html.escape(str(text or ""), quote=True)


def unique_strings(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        key = normalize_text(clean)
        if clean and key not in seen:
            seen.add(key)
            out.append(clean)
    return out


_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


_MONTH_ALIASES = {
    # español
    "enero": 1, "ene": 1, "febrero": 2, "feb": 2, "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4, "mayo": 5, "may": 5, "junio": 6, "jun": 6,
    "julio": 7, "jul": 7, "agosto": 8, "ago": 8, "septiembre": 9,
    "setiembre": 9, "sep": 9, "sept": 9, "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11, "diciembre": 12, "dic": 12,
    # inglés / portugués / italiano / francés, frecuentes en las fuentes
    "january": 1, "jan": 1, "janeiro": 1, "gennaio": 1, "janvier": 1,
    "february": 2, "fevereiro": 2, "febbraio": 2, "fevrier": 2, "février": 2,
    "march": 3, "marco": 3, "março": 3, "marzo": 3, "mars": 3,
    "april": 4, "abril": 4, "aprile": 4, "avril": 4,
    "may": 5, "maio": 5, "maggio": 5, "mai": 5,
    "june": 6, "junho": 6, "giugno": 6, "juin": 6,
    "july": 7, "julho": 7, "luglio": 7, "juillet": 7,
    "august": 8, "agosto": 8, "aout": 8, "août": 8,
    "september": 9, "setembro": 9, "settembre": 9, "septembre": 9,
    "october": 10, "outubro": 10, "ottobre": 10, "octobre": 10,
    "november": 11, "novembro": 11, "novembre": 11,
    "december": 12, "dezembro": 12, "dicembre": 12, "decembre": 12, "décembre": 12,
}


def _normalize_date_text(raw: str) -> str:
    text = unicodedata.normalize("NFD", raw.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("hs.", "").replace("hs", "").replace("h.", ":00")
    return re.sub(r"\s+", " ", text).strip()


def _build_datetime(year: int, month: int, day: int, hour: int, minute: int,
                    second: int, assume_tz) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute, second, tzinfo=assume_tz).astimezone(TZ_AR)
    except (TypeError, ValueError):
        return None


def parse_datetime(value: Any, assume_tz=TZ_AR) -> datetime | None:
    """Parsea fechas editoriales comunes y las normaliza a Buenos Aires.

    Además de ISO admite RFC-822, timestamps Unix, fechas numéricas
    ``dd/mm/yyyy`` y expresiones como ``5 de agosto de 2026, 21:44``. No
    interpreta frases relativas (``hace dos horas``), porque no son una fecha
    auditable y podrían convertir una portada vieja en actualidad.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=assume_tz)
        return dt.astimezone(TZ_AR)

    if isinstance(value, (int, float)):
        try:
            seconds = float(value) / (1000 if abs(float(value)) > 10_000_000_000 else 1)
            return datetime.fromtimestamp(seconds, tz=TZ_AR)
        except (OverflowError, OSError, TypeError, ValueError):
            return None

    raw = str(value).strip()
    if not raw:
        return None

    # Unix timestamp serializado como texto.
    if re.fullmatch(r"\d{10}(?:\.\d+)?|\d{13}", raw):
        try:
            number = float(raw)
            seconds = number / (1000 if len(raw.split(".", 1)[0]) == 13 else 1)
            return datetime.fromtimestamp(seconds, tz=TZ_AR)
        except (OverflowError, OSError, ValueError):
            pass

    # ISO-8601, incluida la forma con espacio entre fecha y hora.
    iso = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=assume_tz)
        return dt.astimezone(TZ_AR)
    except Exception:
        pass

    # RSS/RFC-822.
    try:
        dt = parsedate_to_datetime(raw)
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=assume_tz)
            return dt.astimezone(TZ_AR)
    except Exception:
        pass

    text = _normalize_date_text(raw)
    if any(marker in text for marker in ("hace ", "ago", "minuto", "minute", "hour ago")):
        # ``ago`` es ambiguo con agosto. Solo se rechaza cuando no aparece una
        # fecha numérica o un año que permita auditarla.
        if not re.search(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}", text):
            return None

    # 5 de agosto de 2026, 21:44 / 5 August 2026 21:44.
    month_names = "|".join(sorted((re.escape(name) for name in _MONTH_ALIASES), key=len, reverse=True))
    patterns = (
        rf"\b(\d{{1,2}})\s+(?:de\s+)?({month_names})(?:\s+de)?\s+(\d{{4}})(?:[^0-9]+(\d{{1,2}})[:.]?(\d{{2}})?(?::(\d{{2}}))?)?",
        rf"\b({month_names})\s+(\d{{1,2}})(?:,)?\s+(\d{{4}})(?:[^0-9]+(\d{{1,2}})[:.]?(\d{{2}})?(?::(\d{{2}}))?)?",
    )
    match = re.search(patterns[0], text)
    if match:
        day, month_name, year = int(match.group(1)), match.group(2), int(match.group(3))
        hour = int(match.group(4) or 12)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        return _build_datetime(year, _MONTH_ALIASES[month_name], day, hour, minute, second, assume_tz)
    match = re.search(patterns[1], text)
    if match:
        month_name, day, year = match.group(1), int(match.group(2)), int(match.group(3))
        hour = int(match.group(4) or 12)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        return _build_datetime(year, _MONTH_ALIASES[month_name], day, hour, minute, second, assume_tz)

    # dd/mm/yyyy o dd-mm-yyyy, con hora opcional. Se prioriza el orden usado
    # por los publishers de Argentina, España, Italia, Francia y Brasil.
    match = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})(?:[ t,]+(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?)?\b",
        text,
    )
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
        return _build_datetime(
            year, month, day, int(match.group(4) or 12), int(match.group(5) or 0),
            int(match.group(6) or 0), assume_tz,
        )
    return None


def explicit_date_in_text(text: str, now: datetime | None = None) -> datetime | None:
    """Extrae una fecha calendarizada escrita en un título."""
    now = (now or now_ar()).astimezone(TZ_AR)
    normalized = normalize_text(text)
    raw_text = unicodedata.normalize("NFD", str(text or "").lower())
    raw_text = "".join(ch for ch in raw_text if unicodedata.category(ch) != "Mn")

    months = "|".join(sorted(_MONTHS_ES, key=len, reverse=True))
    match = re.search(rf"\b(\d{{1,2}})\s+de\s+({months})(?:\s+de\s+(\d{{4}}))?\b", normalized)
    if match:
        day = int(match.group(1))
        month = _MONTHS_ES[match.group(2)]
        year = int(match.group(3)) if match.group(3) else now.year
        try:
            candidate = datetime(year, month, day, tzinfo=TZ_AR)
            if not match.group(3) and candidate > now + timedelta(days=45):
                candidate = candidate.replace(year=year - 1)
            return candidate
        except ValueError:
            return None

    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", raw_text)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        raw_year = match.group(3)
        year = now.year if not raw_year else int(raw_year)
        if raw_year and year < 100:
            year += 2000
        try:
            candidate = datetime(year, month, day, tzinfo=TZ_AR)
            if not raw_year and candidate > now + timedelta(days=45):
                candidate = candidate.replace(year=year - 1)
            return candidate
        except ValueError:
            return None
    return None
