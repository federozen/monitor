"""Enriquecimiento de fecha (Fase 2.1).

Sigue el link de una nota, lee su HTML y extrae la fecha de publicación REAL
desde la metadata de la página (JSON-LD, OpenGraph, <time>). Con eso, una fuente
que venía por agregador (Google News, fecha 'para_verificar') pasa a tener una
fecha 'confirmada' y entra al resumen.

`extract_published(html)` es puro y se testea sin red. `enrich_url(url)` es la
parte que toca la red y degrada a (None, None, url) ante cualquier falla.
"""
from __future__ import annotations

import json
from datetime import datetime

from .dates import parse_datetime

try:
    import requests
except Exception:
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None


_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Claves de fecha dentro de un bloque JSON-LD, en orden de preferencia.
_JSONLD_DATE_KEYS = ("datePublished", "dateCreated", "datePosted")
_ARTICLE_TYPES = {"NewsArticle", "Article", "ReportageNewsArticle",
                  "BlogPosting", "WebPage"}


def _walk_for_date(obj) -> str | None:
    """Busca recursivamente una fecha de publicación en un JSON-LD."""
    if isinstance(obj, dict):
        tipo = obj.get("@type")
        tipos = tipo if isinstance(tipo, list) else [tipo]
        if any(t in _ARTICLE_TYPES for t in tipos):
            for k in _JSONLD_DATE_KEYS:
                if obj.get(k):
                    return obj[k]
        for v in obj.values():
            found = _walk_for_date(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _walk_for_date(v)
            if found:
                return found
    return None


def _from_jsonld(soup) -> str | None:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        found = _walk_for_date(data)
        if found:
            return found
    return None


def _from_meta(soup) -> tuple[str, str] | None:
    """OpenGraph / meta / <time>. Devuelve (texto_fecha, origen)."""
    for prop in ("article:published_time", "og:article:published_time"):
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        if tag and tag.get("content"):
            return tag["content"], "opengraph"
    tag = soup.find("meta", attrs={"itemprop": "datePublished"})
    if tag and tag.get("content"):
        return tag["content"], "jsonld"
    t = soup.find("time")
    if t and t.get("datetime"):
        return t["datetime"], "time_tag"
    return None


def extract_published(html: str) -> tuple[datetime | None, str | None]:
    """Extrae (fecha, origen) del HTML de una nota. Puro, sin red.

    origen ∈ {'jsonld','opengraph','time_tag'} — todos mapean a 'confirmada'
    en freshness.DATE_TRUST. Devuelve (None, None) si no encuentra fecha.
    """
    if not html or BeautifulSoup is None:
        return None, None
    soup = BeautifulSoup(html, "html.parser")
    raw = _from_jsonld(soup)
    origen = "jsonld"
    if not raw:
        meta = _from_meta(soup)
        if meta:
            raw, origen = meta
    if not raw:
        return None, None
    fecha = parse_datetime(raw)
    return (fecha, origen) if fecha else (None, None)


def enrich_url(url: str, timeout: int = 12) -> tuple[datetime | None, str | None, str]:
    """Sigue el link (resolviendo redirects) y extrae su fecha real.

    Devuelve (fecha, origen, url_final). Nunca lanza excepción: ante cualquier
    falla (red, timeout, link de Google News que no resuelve) devuelve
    (None, None, url_original) y el llamador conserva la clasificación previa.
    """
    if not (requests and BeautifulSoup) or not url or not url.startswith("http"):
        return None, None, url
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        final = str(resp.url)
        # Si Google News no resolvió al medio real, no hay página que leer.
        if "news.google.com" in final:
            return None, None, final
        if resp.status_code != 200:
            return None, None, final
        fecha, origen = extract_published(resp.text)
        return fecha, origen, final
    except Exception:
        return None, None, url
