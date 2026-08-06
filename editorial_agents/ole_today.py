from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from .utils import explicit_date_in_text, normalize_text, now_ar, parse_datetime, stable_id, unique_strings

_GENERIC = {
    "hora", "juega", "jugar", "como", "ver", "vivo", "online", "partido", "torneo",
    "fecha", "formaciones", "minuto", "minuto", "hoy", "ante", "para", "con", "del",
    "los", "las", "una", "uno", "por", "en", "vs", "contra", "clausura", "apertura",
}


def _tokens(text: str) -> set[str]:
    return {token for token in normalize_text(text).split() if len(token) >= 3 and token not in _GENERIC}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _infer_focus(title: str) -> str:
    text = normalize_text(title)
    rules = [
        ("SERVICIO", ("hora", "como ver", "tv", "formaciones", "agenda")),
        ("RESULTADO", ("gano", "perdio", "empato", "resultado", "gol", "vencio")),
        ("MERCADO", ("refuerzo", "pase", "fichaje", "mercado", "contrato")),
        ("PARTE MEDICO", ("lesion", "baja", "parte medico", "recuperacion", "operado")),
        ("DECLARACIONES", ("dijo", "hablo", "declaracion", "conferencia")),
        ("FORMACION", ("once", "titular", "convocados", "formacion")),
    ]
    for focus, terms in rules:
        if any(term in text for term in terms):
            return focus
    return "INFORMACION"


def _infer_section(url: str, title: str) -> str:
    source = normalize_text(f"{url} {title}")
    rules = [
        ("RIVER", ("/river-plate/", " river ")),
        ("BOCA", ("/boca-juniors/", " boca ")),
        ("SELECCION", ("/seleccion-argentina/", "seleccion argentina", "messi")),
        ("INTERNACIONAL", ("/futbol-internacional/", "champions", "premier league")),
        ("AUTOS", ("/autos/", "formula 1", "turismo carretera", "colapinto")),
        ("TENIS", ("/tenis/", "atp", "wta", "tenis")),
        ("RUGBY", ("/rugby/", "rugby", "pumas")),
        ("BASQUET", ("/basquet/", "nba", "basquet")),
    ]
    padded = f" {source} "
    for section, terms in rules:
        if any(term in padded for term in terms):
            return section
    return "OTROS"


def _entities(title: str) -> list[str]:
    try:
        from monitor_core import detectar_entidades
        return list(detectar_entidades(title) or [])
    except Exception:
        return []


def _first_seen_map(previous: list[dict] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in previous or []:
        key = str(row.get("URL") or row.get("url") or normalize_text(str(row.get("Titulo") or row.get("title") or ""))).strip()
        first = str(row.get("PrimeraDeteccion") or row.get("first_seen") or "").strip()
        if key and first:
            result[key] = first
    return result


def _record_type(item: dict, title: str, now: datetime) -> tuple[str, str]:
    published = parse_datetime(item.get("fecha_publicacion") or item.get("fecha"))
    updated = parse_datetime(item.get("fecha_actualizacion") or item.get("actualizado"))
    explicit = explicit_date_in_text(title, now)
    origin = str(item.get("ole_origin") or item.get("origen_ole") or "ultimas").lower()
    if explicit is not None and explicit.date() != now.date():
        return "", "FECHA_EXPLICITA_ANTERIOR"
    if origin == "gnews":
        return "", "AGREGADOR_NO_CERTIFICA_FECHA"
    if published is not None and published.date() == now.date():
        return "PUBLICADA_HOY", "CONFIRMADA"
    if updated is not None and updated.date() == now.date():
        return "ACTUALIZADA_HOY", "CONFIRMADA"
    return "", "SIN_FECHA_DEL_DIA"


def _belongs_to_today(item: dict, title: str, first_seen_value: str, now: datetime) -> bool:
    record_type, _ = _record_type(item, title, now)
    return bool(record_type)


def _group_compatible(entry: dict, group: dict) -> tuple[bool, float]:
    entities = set(entry.get("entities") or [])
    group_entities = set(group.get("entities") or [])
    base = max(_similarity(entry["title"], member["title"]) for member in group["members"])
    if entities and group_entities and not (entities & group_entities):
        # Evita agrupar servicios genéricos de River y Boca solo porque comparten
        # "hora", "cómo ver" y "Torneo Clausura".
        return False, base
    if entities & group_entities:
        base += 0.18
    same_section = entry.get("section") == group.get("section") and entry.get("section") not in {"OTROS", "INTERNACIONAL"}
    if same_section:
        base += 0.08
    return base >= 0.46, base


def build_ole_today(ole_items: list[dict] | None, previous: list[dict] | None = None,
                    recommendations: list[dict] | None = None,
                    now: datetime | None = None) -> tuple[list[dict], list[dict]]:
    now = now or now_ar()
    now_iso = now.isoformat(timespec="seconds")
    first_seen = _first_seen_map(previous)
    recommendation_by_ole_url: dict[str, list[dict]] = defaultdict(list)
    recommendation_by_ole_title: list[dict] = []
    for rec in recommendations or []:
        url = str(rec.get("ole_match_url") or "").strip()
        if url:
            recommendation_by_ole_url[url].append(rec)
        if rec.get("ole_match_title"):
            recommendation_by_ole_title.append(rec)

    entries: list[dict] = []
    seen: set[str] = set()
    seen_titles: set[str] = set()
    for item in ole_items or []:
        title = str(item.get("titulo") or item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if len(title) < 8:
            continue
        normalized_title = normalize_text(title)
        key = url or normalized_title
        if not key or key in seen or (normalized_title and normalized_title in seen_titles):
            continue
        first_seen_value = first_seen.get(key, now_iso)
        record_type, date_confidence = _record_type(item, title, now)
        if not record_type:
            continue
        seen.add(key)
        seen_titles.add(normalized_title)

        related = list(recommendation_by_ole_url.get(url, []))
        if not related:
            scored = []
            for rec in recommendation_by_ole_title:
                score = _similarity(title, str(rec.get("ole_match_title") or ""))
                if score >= 0.45:
                    scored.append((score, rec))
            related = [pair[1] for pair in sorted(scored, key=lambda pair: pair[0], reverse=True)[:3]]
        actions = unique_strings([str(rec.get("action") or "") for rec in related if rec.get("action")])
        external = unique_strings([str(rec.get("title") or "") for rec in related if rec.get("title")])
        section = _infer_section(url, title)
        entries.append({
            "ole_id": stable_id(key, "ole"),
            "first_seen": first_seen_value,
            "last_seen": now_iso,
            "record_type": record_type,
            "date_confidence": date_confidence,
            "origin": str(item.get("ole_origin") or item.get("origen_ole") or "ultimas"),
            "source_page": item.get("ole_page", ""),
            "published_at": str(item.get("fecha_publicacion") or item.get("fecha") or ""),
            "updated_at": str(item.get("fecha_actualizacion") or item.get("actualizado") or ""),
            "section": section,
            "topic_id": "",
            "topic": "",
            "focus": _infer_focus(title),
            "title": title,
            "url": url,
            "entities": _entities(title),
            "related_external": external,
            "suggested_action": " | ".join(actions),
        })

    groups: list[dict[str, Any]] = []
    for entry in entries:
        best_group = None
        best_score = 0.0
        for group in groups:
            compatible, score = _group_compatible(entry, group)
            if compatible and score > best_score:
                best_score, best_group = score, group
        if best_group is not None:
            best_group["members"].append(entry)
            best_group["entities"] = unique_strings(best_group["entities"] + entry.get("entities", []))
        else:
            groups.append({
                "members": [entry], "entities": list(entry.get("entities") or []),
                "section": entry.get("section"),
            })

    coverage_rows: list[dict] = []
    for group in groups:
        members = group["members"]
        representative = max(members, key=lambda item: (len(item.get("related_external") or []), len(item["title"])))
        entity_key = "|".join(sorted(normalize_text(x) for x in group.get("entities") or [] if x))
        token_key = "|".join(sorted(_tokens(representative["title"])))
        topic_id = stable_id(entity_key or token_key or representative["title"], "ot")
        topic = representative["title"]
        all_external = unique_strings([x for item in members for x in item.get("related_external", [])])
        actions = unique_strings([item.get("suggested_action", "") for item in members if item.get("suggested_action")])
        for entry in members:
            entry["topic_id"] = topic_id
            entry["topic"] = topic

        def event_time(item: dict):
            return parse_datetime(item.get("updated_at")) or parse_datetime(item.get("published_at")) or parse_datetime(item.get("first_seen")) or now

        latest_member = max(members, key=event_time)
        coverage_rows.append({
            "topic_id": topic_id,
            "topic": topic,
            "piece_count": len(members),
            "published_today": sum(1 for item in members if item.get("record_type") == "PUBLICADA_HOY"),
            "updated_today": sum(1 for item in members if item.get("record_type") == "ACTUALIZADA_HOY"),
            "sections": unique_strings([item.get("section", "") for item in members]),
            "focuses": unique_strings([item.get("focus", "") for item in members]),
            "first_seen": min(item.get("first_seen", now_iso) for item in members),
            "last_seen": max(item.get("last_seen", now_iso) for item in members),
            "last_title": latest_member["title"],
            "last_url": latest_member["url"],
            "titles": [item["title"] for item in members],
            "external_updates": all_external,
            "suggested_action": " | ".join(actions) if actions else "YA CUBIERTO / SEGUIR",
            "overcoverage": len(members) >= 5,
        })

    entries.sort(key=lambda item: (parse_datetime(item.get("updated_at")) or parse_datetime(item.get("published_at")) or now, item.get("title", "")), reverse=True)
    coverage_rows.sort(key=lambda item: (-item["piece_count"], item["topic"]))
    return entries, coverage_rows
