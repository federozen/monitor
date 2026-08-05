from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Source:
    source_id: str
    name: str
    country: str = "AR"
    language: str = "es"
    category: str = "medio"
    priority: int = 50
    source_type: str = "media"
    primary_method: str = "rss"
    fallback_method: str | None = None
    url: str = ""
    status: str = "active"
    unique_value: str = ""


@dataclass
class Article:
    article_id: str
    title: str
    url: str
    canonical_url: str = ""
    publisher: str = ""
    discovery_channel: str = "direct"
    date_published: datetime | None = None
    date_updated: datetime | None = None
    date_detected: datetime | None = None
    date_origin: str = "missing"
    date_confidence: str = "para_verificar"
    section: str = ""
    entities: list[str] = field(default_factory=list)
    sport: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass
class Story:
    story_id: str
    title: str
    articles: list[Article] = field(default_factory=list)
    first_seen: datetime | None = None
    last_change: datetime | None = None
    official_confirmed: bool = False
    ole_status: str = "NO_EVALUADO"
    state: str = "abierta"
    changes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Cut:
    cut_id: str
    started_at: datetime
    ended_at: datetime
    stories: list[Story] = field(default_factory=list)
    source_health: list[dict[str, Any]] = field(default_factory=list)
    quality_state: str = "SIN_EVALUAR"
    preserve_previous: bool = False

