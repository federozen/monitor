from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .dates import in_window, parse_datetime
from .models import Article


DATE_TRUST = {
    "datePublished": ("confirmada", "metadata_directa"),
    "jsonld": ("confirmada", "metadata_directa"),
    "opengraph": ("confirmada", "metadata_directa"),
    "time_tag": ("confirmada", "metadata_directa"),
    "rss": ("probable", "rss_directo"),
    "publisher_listing": ("probable", "listado_directo"),
    "discovery_timestamp": ("para_verificar", "agregador"),
    "missing": ("para_verificar", "sin_fecha"),
}


def classify_article(article: Article) -> Article:
    confidence, origin = DATE_TRUST.get(article.date_origin, ("para_verificar", article.date_origin or "desconocido"))
    return replace(article, date_confidence=confidence, date_origin=origin)


def usable_for_summary(article: Article, now: datetime, hours: int = 4) -> bool:
    checked = classify_article(article)
    moment = checked.date_published or checked.date_updated
    return checked.date_confidence in {"confirmada", "probable"} and in_window(moment, now, hours)


def classify_ole_item(article: Article, now: datetime) -> str:
    published = parse_datetime(article.date_published)
    updated = parse_datetime(article.date_updated)
    current = parse_datetime(now)
    if not current:
        return "PARA_VERIFICAR"
    if published and published.date() == current.date():
        return "PUBLICADA_HOY"
    if updated and updated.date() == current.date():
        return "ACTUALIZADA_HOY"
    return "HISTORICA_PARA_COMPARAR"

