"""Enriquecimiento acotado de fechas de artículos.

El scraper de portadas es rápido, pero muchas tarjetas no exponen hora. Este
módulo abre solamente un conjunto priorizado de notas directas y recupera
``datePublished`` / ``dateModified`` desde metadata auditable. Nunca usa la
hora de Google News como fecha editorial.
"""
from __future__ import annotations

import base64
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .utils import TZ_AR, normalize_text, now_ar, parse_datetime

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
}

_ARTICLE_TYPES = {
    "article", "newsarticle", "reportagenewsarticle", "blogposting",
    "liveblogposting", "analysisnewsarticle", "reviewnewsarticle",
}
_PUBLISHED_KEYS = (
    "datePublished", "dateCreated", "uploadDate", "datePosted", "date",
)
_UPDATED_KEYS = (
    "dateModified", "dateUpdated", "lastReviewed", "lastModified",
)
_PUBLISHED_META = (
    ("property", "article:published_time"),
    ("property", "og:published_time"),
    ("name", "article:published_time"),
    ("name", "datePublished"),
    ("name", "publish-date"),
    ("name", "pub_date"),
    ("name", "parsely-pub-date"),
    ("name", "sailthru.date"),
    ("name", "dc.date"),
    ("name", "dcterms.created"),
    ("itemprop", "datePublished"),
)
_UPDATED_META = (
    ("property", "article:modified_time"),
    ("property", "og:updated_time"),
    ("name", "dateModified"),
    ("name", "last-modified"),
    ("name", "parsely-modified-date"),
    ("itemprop", "dateModified"),
)

_OFFICIAL_SOURCE_HINTS = {
    "afa", "conmebol", "fifa", "uefa", "uar", "cab", "aat", "actc",
    "ligapro", "olympics",
}
_PRIORITY_TITLE_HINTS = {
    "confirmado", "oficial", "lesion", "baja", "sancion", "resultado",
    "formacion", "convocados", "suspendido", "postergado", "fecha", "horario",
    "river", "boca", "seleccion", "messi", "racing", "independiente",
}


def _clean_type(value: Any) -> set[str]:
    values = value if isinstance(value, list) else [value]
    return {normalize_text(str(item)).replace(" ", "") for item in values if item}


def _walk_jsonld(value: Any, published: list[Any], updated: list[Any], article_context: bool = False) -> None:
    if isinstance(value, list):
        for item in value:
            _walk_jsonld(item, published, updated, article_context)
        return
    if not isinstance(value, dict):
        return
    own_article = bool(_clean_type(value.get("@type")) & _ARTICLE_TYPES)
    context = article_context or own_article
    if context:
        for key in _PUBLISHED_KEYS:
            if value.get(key):
                published.append(value.get(key))
                break
        for key in _UPDATED_KEYS:
            if value.get(key):
                updated.append(value.get(key))
                break
    for child in value.values():
        if isinstance(child, (dict, list)):
            _walk_jsonld(child, published, updated, context)


def _first_parsed(values: list[Any]) -> datetime | None:
    for value in values:
        parsed = parse_datetime(value)
        if parsed:
            return parsed
    return None


def _meta_value(soup: BeautifulSoup, definitions: tuple[tuple[str, str], ...]) -> tuple[Any, str] | tuple[None, None]:
    for attr, name in definitions:
        tag = soup.find("meta", attrs={attr: re.compile(rf"^{re.escape(name)}$", re.I)})
        if tag:
            raw = tag.get("content") or tag.get("value")
            if raw:
                return raw, f"meta:{name}"
    return None, None


def _time_value(soup: BeautifulSoup, updated: bool = False) -> tuple[Any, str] | tuple[None, None]:
    selectors = (
        "time[itemprop='dateModified']", "time[class*='update']", "time[class*='modif']"
    ) if updated else (
        "time[itemprop='datePublished']", "time[class*='publish']", "time[class*='date']", "time"
    )
    for selector in selectors:
        for tag in soup.select(selector):
            raw = tag.get("datetime") or tag.get("content") or tag.get_text(" ", strip=True)
            if parse_datetime(raw):
                return raw, f"time:{selector}"
    return None, None


def extract_article_dates(html: str) -> dict[str, Any]:
    """Extrae fechas publicadas/modificadas desde HTML sin tocar la red."""
    result = {
        "published_at": None,
        "updated_at": None,
        "published_origin": "",
        "updated_origin": "",
    }
    if not html:
        return result
    soup = BeautifulSoup(html, "html.parser")

    published_raw: list[Any] = []
    updated_raw: list[Any] = []
    for script in soup.find_all("script", type=re.compile(r"application/ld\+json", re.I)):
        text = script.string or script.get_text("", strip=True)
        if not text:
            continue
        try:
            data = json.loads(text)
        except Exception:
            # Algunos sitios agregan comentarios o varios objetos separados.
            match = re.search(r"(\{.*\}|\[.*\])", text, re.S)
            if not match:
                continue
            try:
                data = json.loads(match.group(1))
            except Exception:
                continue
        _walk_jsonld(data, published_raw, updated_raw)

    published = _first_parsed(published_raw)
    updated = _first_parsed(updated_raw)
    if published:
        result["published_at"] = published
        result["published_origin"] = "jsonld:datePublished"
    if updated:
        result["updated_at"] = updated
        result["updated_origin"] = "jsonld:dateModified"

    if not result["published_at"]:
        raw, origin = _meta_value(soup, _PUBLISHED_META)
        parsed = parse_datetime(raw)
        if parsed:
            result["published_at"] = parsed
            result["published_origin"] = origin
    if not result["updated_at"]:
        raw, origin = _meta_value(soup, _UPDATED_META)
        parsed = parse_datetime(raw)
        if parsed:
            result["updated_at"] = parsed
            result["updated_origin"] = origin

    if not result["published_at"]:
        raw, origin = _time_value(soup, updated=False)
        parsed = parse_datetime(raw)
        if parsed:
            result["published_at"] = parsed
            result["published_origin"] = origin
    if not result["updated_at"]:
        raw, origin = _time_value(soup, updated=True)
        parsed = parse_datetime(raw)
        if parsed:
            result["updated_at"] = parsed
            result["updated_origin"] = origin
    return result


def _embedded_google_url(url: str) -> str:
    """Decodifica únicamente el formato antiguo que contenía la URL literal.

    Los identificadores nuevos de Google News requieren una llamada privada y
    no se tratan como fuente primaria. Si no hay una URL auditable, se devuelve
    vacío y la noticia continúa como ``discovery_timestamp``.
    """
    if "news.google.com" not in str(url):
        return str(url or "")
    match = re.search(r"/articles/([^?/#]+)", str(url))
    if not match:
        return ""
    token = match.group(1)
    try:
        decoded = base64.urlsafe_b64decode(token + "=" * ((4 - len(token) % 4) % 4))
    except Exception:
        return ""
    found = re.search(rb"https?://[^\x00-\x20\"<>]+", decoded)
    return found.group(0).decode("utf-8", "ignore") if found else ""


def _valid_article_url(url: str) -> bool:
    if not url or not url.startswith(("http://", "https://")):
        return False
    if "news.google.com" in url:
        return bool(_embedded_google_url(url))
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not parsed.netloc or len(path) < 6:
        return False
    bad = ("/tag/", "/autor/", "/author/", "/search", "/buscar", "/categoria/")
    return not any(piece in path.lower() for piece in bad)


def fetch_article_dates(url: str, timeout: int = 8, session: requests.Session | None = None) -> dict[str, Any]:
    result = {
        "published_at": None, "updated_at": None, "published_origin": "",
        "updated_origin": "", "final_url": str(url or ""), "status": "error",
    }
    target = _embedded_google_url(url) if "news.google.com" in str(url) else str(url or "")
    if not _valid_article_url(target):
        result["status"] = "unsupported_url"
        return result
    client = session or requests
    try:
        response = client.get(target, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        result["final_url"] = str(response.url or target)
        content_type = str(response.headers.get("content-type") or "").lower()
        if response.status_code != 200:
            result["status"] = f"http_{response.status_code}"
            return result
        if content_type and "html" not in content_type and "xhtml" not in content_type:
            result["status"] = "not_html"
            return result
        dates = extract_article_dates(response.text)
        result.update(dates)
        result["status"] = "ok" if dates.get("published_at") or dates.get("updated_at") else "no_date"
        return result
    except Exception as exc:
        result["status"] = type(exc).__name__
        return result


def _has_clock(value: Any) -> bool:
    raw = str(value or "").strip().lower()
    if not raw:
        return False
    if re.search(r"t\d{1,2}:\d{2}|\b\d{1,2}:\d{2}(?::\d{2})?\b", raw):
        return True
    # RFC-822 casi siempre contiene HH:MM:SS.
    return bool(re.search(r"\b\d{1,2}\s+[a-z]{3}\s+\d{4}\s+\d{2}:\d{2}", raw))


def _source_priority(source_id: str, source: dict, news: dict) -> int:
    score = 0
    if source_id in _OFFICIAL_SOURCE_HINTS or "oficial" in normalize_text(str(source.get("nombre") or "")):
        score += 35
    if str(source.get("zona") or "").lower() == "nacional":
        score += 12
    title = normalize_text(str(news.get("titulo") or ""))
    score += min(24, sum(4 for hint in _PRIORITY_TITLE_HINTS if hint in title))
    if not news.get("fecha_publicacion"):
        score += 12
    if str(news.get("date_trust") or "") == "publisher_date_only":
        score += 8
    if news.get("publisher_original"):
        score += 3
    return score


def _normalize_existing(news: dict) -> bool:
    raw = news.get("fecha_publicacion")
    parsed = parse_datetime(raw)
    if not parsed:
        return False
    trust = str(news.get("date_trust") or "").lower()
    if trust == "discovery_timestamp":
        # Se normaliza el formato, pero nunca se asciende la confianza.
        news["fecha_publicacion"] = parsed.isoformat(timespec="seconds")
        return True
    if not _has_clock(raw):
        news["date_trust"] = "publisher_date_only"
        news.setdefault("date_origin", "publisher_listing_date_only")
    elif trust in {"", "missing", "unverified"}:
        news["date_trust"] = "publisher_timestamp"
        news.setdefault("date_origin", "publisher_listing")
    news["fecha_publicacion"] = parsed.isoformat(timespec="seconds")
    return True


def enrich_results_dates(results: dict[str, list[dict]], sources: list[dict], *,
                         max_articles: int | None = None, timeout: int | None = None,
                         workers: int | None = None, now: datetime | None = None,
                         fetcher=fetch_article_dates) -> dict[str, int]:
    """Normaliza fechas existentes y abre un tope de artículos sin hora.

    Modifica ``results`` in-place. El tope y el paralelismo evitan que una fuente
    lenta convierta el monitor en un crawler indiscriminado.
    """
    if str(os.environ.get("DATE_ENRICH_ENABLED", "true")).strip().lower() in {"0", "false", "no", "off"}:
        return {"normalized": 0, "requested": 0, "confirmed": 0, "updated": 0, "failed": 0}

    max_articles = max(0, min(120, int(max_articles if max_articles is not None else os.environ.get("DATE_ENRICH_MAX_ARTICLES", "48") or 48)))
    timeout = max(3, min(20, int(timeout if timeout is not None else os.environ.get("DATE_ENRICH_TIMEOUT", "8") or 8)))
    workers = max(1, min(8, int(workers if workers is not None else os.environ.get("DATE_ENRICH_WORKERS", "6") or 6)))
    current = (now or now_ar()).astimezone(TZ_AR)
    source_map = {str(source.get("id") or ""): source for source in sources or []}

    normalized = 0
    candidates: dict[str, list[tuple[str, dict]]] = {}
    priorities: dict[str, int] = {}
    for source_id, items in (results or {}).items():
        source = source_map.get(str(source_id), {})
        for news in items or []:
            if _normalize_existing(news):
                normalized += 1
            trust = str(news.get("date_trust") or "missing").lower()
            has_exact = bool(parse_datetime(news.get("fecha_publicacion"))) and trust not in {
                "missing", "unverified", "publisher_date_only",
            }
            if has_exact:
                continue
            url = str(news.get("url") or "")
            if not _valid_article_url(url):
                continue
            # La URL nueva de Google News no es una evidencia primaria y no se
            # consulta salvo que contenga una URL literal decodificable.
            target = _embedded_google_url(url) if "news.google.com" in url else url
            if not target:
                continue
            candidates.setdefault(target, []).append((str(source_id), news))
            priorities[target] = max(priorities.get(target, -999), _source_priority(str(source_id), source, news))

    selected = sorted(candidates, key=lambda url: (-priorities.get(url, 0), url))[:max_articles]
    stats = {"normalized": normalized, "requested": len(selected), "confirmed": 0, "updated": 0, "failed": 0}
    if not selected:
        return stats

    fetched: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetcher, url, timeout): url for url in selected}
        for future in as_completed(futures):
            url = futures[future]
            try:
                fetched[url] = future.result() or {}
            except Exception as exc:  # un fetch defectuoso no rompe el corte
                fetched[url] = {"status": type(exc).__name__}

    future_limit = current + timedelta(hours=2)
    oldest_reasonable = current - timedelta(days=3660)
    for target in selected:
        result = fetched.get(target, {})
        published = parse_datetime(result.get("published_at"))
        updated = parse_datetime(result.get("updated_at"))
        if published and not (oldest_reasonable <= published <= future_limit):
            published = None
        if updated and not (oldest_reasonable <= updated <= future_limit):
            updated = None
        if not published and not updated:
            stats["failed"] += 1
            continue
        for _source_id, news in candidates.get(target, []):
            if published:
                news["fecha_publicacion"] = published.isoformat(timespec="seconds")
                news["fecha_publicacion_verificada"] = news["fecha_publicacion"]
                news["date_trust"] = "article_metadata"
                news["date_origin"] = str(result.get("published_origin") or "article_metadata")
                stats["confirmed"] += 1
            if updated:
                news["fecha_actualizacion"] = updated.isoformat(timespec="seconds")
                news["update_origin"] = str(result.get("updated_origin") or "article_metadata")
                stats["updated"] += 1
            final_url = str(result.get("final_url") or "")
            if final_url and "news.google.com" not in final_url:
                news["url_final"] = final_url
    return stats


def enrich_cluster_dates(themes: list[dict], *, max_clusters: int | None = None,
                         max_articles: int | None = None, timeout: int | None = None,
                         workers: int | None = None, now: datetime | None = None,
                         fetcher=fetch_article_dates) -> dict[str, int]:
    """Verifica al menos una nota directa por historia todavía sin fecha fiable.

    La primera pasada trabaja por fuente y puede concentrar consultas en varias
    notas del mismo tema. Esta segunda pasada se ejecuta después del clustering
    y reparte el presupuesto entre historias distintas. Modifica las noticias
    referenciadas por cada cluster *in-place*, por lo que el resumen editorial
    recibe las fechas sin reconstruir los clusters.
    """
    if str(os.environ.get("DATE_ENRICH_ENABLED", "true")).strip().lower() in {"0", "false", "no", "off"}:
        return {
            "clusters_considered": 0, "clusters_requested": 0,
            "clusters_confirmed": 0, "requested": 0,
            "confirmed": 0, "updated": 0, "failed": 0,
        }

    max_clusters = max(0, min(120, int(
        max_clusters if max_clusters is not None
        else os.environ.get("DATE_ENRICH_CLUSTER_MAX", "60") or 60
    )))
    max_articles = max(0, min(160, int(
        max_articles if max_articles is not None
        else os.environ.get("DATE_ENRICH_CLUSTER_ARTICLES", "72") or 72
    )))
    timeout = max(3, min(20, int(
        timeout if timeout is not None
        else os.environ.get("DATE_ENRICH_TIMEOUT", "8") or 8
    )))
    workers = max(1, min(8, int(
        workers if workers is not None
        else os.environ.get("DATE_ENRICH_WORKERS", "6") or 6
    )))
    current = (now or now_ar()).astimezone(TZ_AR)
    untrusted = {"", "missing", "unverified", "publisher_date_only", "discovery_timestamp"}

    cluster_options: list[tuple[int, str, list[tuple[int, str, dict]]]] = []
    considered = 0
    for position, theme in enumerate((themes or [])[:max_clusters]):
        entries = theme.get("noticias") or []
        if not isinstance(entries, list):
            continue
        considered += 1
        already_trusted = False
        options: list[tuple[int, str, dict]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            news = entry.get("noticia") if isinstance(entry.get("noticia"), dict) else entry
            source = entry.get("fuente") if isinstance(entry.get("fuente"), dict) else {}
            trust = str(news.get("date_trust") or "").lower()
            published = parse_datetime(
                news.get("fecha_publicacion_verificada") or news.get("fecha_publicacion")
            )
            updated = parse_datetime(news.get("fecha_actualizacion"))
            if (published or updated) and trust not in untrusted:
                already_trusted = True
                break

            raw_url = str(news.get("url_final") or news.get("url") or "")
            target = _embedded_google_url(raw_url) if "news.google.com" in raw_url else raw_url
            if not _valid_article_url(target):
                continue
            source_id = str(news.get("source_id") or source.get("id") or "")
            score = _source_priority(source_id, source, news)
            if "news.google.com" not in raw_url:
                score += 22
            channel = normalize_text(str(news.get("discovery_channel") or ""))
            if channel and channel != "google news":
                score += 10
            # Un cluster con más publishers merece gastar antes una consulta.
            score += min(18, int(theme.get("cant_medios") or 0) * 3)
            options.append((score, target, news))
        if already_trusted or not options:
            continue
        options.sort(key=lambda item: (-item[0], item[1]))
        cluster_key = str(theme.get("titulo") or f"cluster_{position}")
        cluster_options.append((position, cluster_key, options))

    # Primera ronda: una URL por historia. Segunda: respaldo para las historias
    # que todavía tengan otra fuente directa, hasta agotar el presupuesto.
    selected: list[str] = []
    refs_by_url: dict[str, list[dict]] = {}
    cluster_by_url: dict[str, set[str]] = {}
    seen_urls: set[str] = set()
    for round_index in (0, 1):
        for _position, cluster_key, options in cluster_options:
            if len(selected) >= max_articles:
                break
            if round_index >= len(options):
                continue
            _score, url, news = options[round_index]
            refs_by_url.setdefault(url, []).append(news)
            cluster_by_url.setdefault(url, set()).add(cluster_key)
            if url not in seen_urls:
                selected.append(url)
                seen_urls.add(url)
        if len(selected) >= max_articles:
            break

    stats = {
        "clusters_considered": considered,
        "clusters_requested": len({key for url in selected for key in cluster_by_url.get(url, set())}),
        "clusters_confirmed": 0,
        "requested": len(selected), "confirmed": 0, "updated": 0, "failed": 0,
    }
    if not selected:
        return stats

    fetched: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetcher, url, timeout): url for url in selected}
        for future in as_completed(futures):
            url = futures[future]
            try:
                fetched[url] = future.result() or {}
            except Exception as exc:
                fetched[url] = {"status": type(exc).__name__}

    future_limit = current + timedelta(hours=2)
    oldest_reasonable = current - timedelta(days=3660)
    confirmed_clusters: set[str] = set()
    for target in selected:
        result = fetched.get(target, {})
        published = parse_datetime(result.get("published_at"))
        updated = parse_datetime(result.get("updated_at"))
        if published and not (oldest_reasonable <= published <= future_limit):
            published = None
        if updated and not (oldest_reasonable <= updated <= future_limit):
            updated = None
        if not published and not updated:
            stats["failed"] += 1
            continue
        confirmed_clusters.update(cluster_by_url.get(target, set()))
        for news in refs_by_url.get(target, []):
            if published:
                news["fecha_publicacion"] = published.isoformat(timespec="seconds")
                news["fecha_publicacion_verificada"] = news["fecha_publicacion"]
                news["date_trust"] = "article_metadata"
                news["date_origin"] = str(result.get("published_origin") or "article_metadata")
                stats["confirmed"] += 1
            if updated:
                news["fecha_actualizacion"] = updated.isoformat(timespec="seconds")
                news["update_origin"] = str(result.get("updated_origin") or "article_metadata")
                stats["updated"] += 1
            final_url = str(result.get("final_url") or "")
            if final_url and "news.google.com" not in final_url:
                news["url_final"] = final_url
    stats["clusters_confirmed"] = len(confirmed_clusters)
    return stats
