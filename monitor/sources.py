"""Lectura de fuentes reales (RSS) hacia el modelo Article del núcleo.

Este módulo es el único que toca la red del lado de "entrada". Todo lo demás
del núcleo (freshness, cluster, recomendaciones) sigue siendo puro y testeable
sin red. Cada feed que falla se reporta como fuente caída, sin romper la corrida
completa: eso alimenta la lógica de corte degradado de snapshots.py.

Las fuentes se editan en `sources.json` (sin tocar código), coherente con la
filosofía del proyecto: el editor cambia la lista sin programar.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except Exception:  # sin requests: modo degradado, el runner avisa
    requests = None

try:
    import feedparser
except Exception:
    feedparser = None

from .config import TZ_AR
from .enrich import enrich_url
from .models import Article


_UA = "Mozilla/5.0 (compatible; MonitorDeportivo/2.0; +https://example.local)"


def _article_id(url: str, title: str) -> str:
    base = (url or title or "").encode("utf-8", "ignore")
    return "art_" + hashlib.sha1(base).hexdigest()[:12]


def _entry_datetime(entry) -> datetime | None:
    """Convierte la fecha del feed (struct_time UTC) a datetime con tz AR."""
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            dt_utc = datetime(*parsed[:6], tzinfo=timezone.utc)
            return dt_utc.astimezone(TZ_AR)
    return None


def _fetch_one(feed: dict, timeout: int) -> tuple[list[Article], dict]:
    """Devuelve (articulos, salud) para un feed. Nunca lanza excepción."""
    source_id = feed.get("source_id") or feed.get("publisher", "desconocido")
    publisher = feed.get("publisher", source_id)
    url = feed.get("url", "")
    origin = feed.get("date_origin", "rss")
    salud = {"source_id": source_id, "status": "error", "count": 0}

    if not (requests and feedparser and url):
        salud["reason"] = "sin_dependencias_o_url"
        return [], salud

    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": _UA})
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        articulos = []
        for entry in parsed.entries:
            link = getattr(entry, "link", "") or ""
            title = (getattr(entry, "title", "") or "").strip()
            if not title:
                continue
            articulos.append(Article(
                article_id=_article_id(link, title),
                title=title,
                url=link,
                publisher=publisher,
                discovery_channel="rss",
                date_published=_entry_datetime(entry),
                date_origin=origin,
            ))
        salud["status"] = "ok" if articulos else "vacio"
        salud["count"] = len(articulos)
        return articulos, salud
    except Exception as exc:  # red caída, timeout, feed roto
        salud["reason"] = type(exc).__name__
        return [], salud


class RSSFetcher:
    """Lee todas las fuentes de sources.json y separa Olé para la comparación.

    Expone .fetch() -> (articulos, ole_titles, source_health), la interfaz que
    consume pipeline.run_pipeline(). Es inyectable: los tests pasan un fake con
    la misma firma y no tocan la red.
    """

    def __init__(self, config_path: str | Path, timeout: int = 12,
                 enrich_cap: int = 40):
        self.config_path = Path(config_path)
        self.timeout = timeout
        self.enrich_cap = enrich_cap  # tope de notas a enriquecer por corrida

    def _load(self) -> dict:
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _enrich(self, articulos: list[Article], restante: int) -> tuple[list[Article], int]:
        """Sigue el link de cada nota y reemplaza su fecha por la real. Devuelve
        (articulos_actualizados, enriquecidas). Respeta el tope global `restante`."""
        salida, hechas = [], 0
        for art in articulos:
            if hechas >= restante:
                salida.append(art)
                continue
            fecha, origen, _final = enrich_url(art.url, self.timeout)
            if fecha and origen:
                salida.append(replace(art, date_published=fecha, date_origin=origen))
                hechas += 1
            else:
                salida.append(art)  # no se pudo: conserva la clasificación previa
        return salida, hechas

    def fetch(self) -> tuple[list[Article], list[str], list[dict]]:
        cfg = self._load()
        articulos: list[Article] = []
        salud: list[dict] = []
        ole_titles: list[str] = []
        presupuesto = self.enrich_cap

        # Olé se lee como comparación, no como fuente propia a publicar.
        ole = cfg.get("ole")
        if ole and ole.get("url"):
            ole_arts, ole_salud = _fetch_one({**ole, "publisher": "Olé"}, self.timeout)
            ole_titles = [a.title for a in ole_arts]
            salud.append({**ole_salud, "source_id": "ole"})

        for feed in cfg.get("feeds", []):
            arts, s = _fetch_one(feed, self.timeout)
            if feed.get("enrich") and arts and presupuesto > 0:
                arts, hechas = self._enrich(arts, presupuesto)
                presupuesto -= hechas
                s["enriquecidas"] = hechas
            articulos.extend(arts)
            salud.append(s)

        return articulos, ole_titles, salud
