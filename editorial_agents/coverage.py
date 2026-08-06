from __future__ import annotations

import re
from typing import Any

from .utils import normalize_text, unique_strings

STATUS_WORDS = {
    "confirmado", "oficial", "descartado", "lesion", "lesionado", "baja",
    "suspendido", "sancion", "renuncio", "despedido", "fallecio", "murio",
    "acuerdo", "firmo", "firma", "presentado", "convocado", "titular",
    "diagnostico", "operado", "recuperacion", "fecha", "horario", "sede",
    "resultado", "gol", "clasifico", "eliminado", "campeon", "semanas",
    "meses", "dias", "millones", "euros", "dolares", "contrato", "resciso",
    "operacion", "cirugia", "reemplazo", "suplente", "capitan", "desmentido",
}

GENERIC_WORDS = {
    "partido", "equipo", "futbol", "club", "jugador", "tecnico", "liga",
    "resultado", "resultados", "marcador", "cronica",
    "copa", "torneo", "fecha", "hoy", "manana", "ultimo", "ultima", "nueva", "nuevo",
    "tras", "ante", "para", "con", "sin", "sobre", "desde", "vivo", "hora",
    "como", "ver", "juega", "jugar", "online", "minuto", "formaciones",
    "por", "del", "las", "los", "una", "uno", "unos", "unas", "que", "esta",
    "este", "sus", "the", "and", "for", "with", "from", "after", "before",
    "today", "live", "watch", "report", "news", "latest", "football", "soccer",
}

COVERAGE_ALIASES = {
    "CUBIERTO_IGUAL": "YA_CUBIERTO",
    "CUBIERTO_CON_NOVEDAD": "CUBIERTO_CON_DATO_NUEVO",
    "CUBIERTO_PARCIAL": "CUBIERTO_PARCIALMENTE",
}

# Entidades internacionales frecuentes que no están en el diccionario local de
# monitor_core. Se exige más de una señal para evitar que una sola palabra como
# "Arsenal" vincule dos historias completamente diferentes.
_ENTITY_ALIASES = {
    "arsenal": ("arsenal",), "betis": ("betis", "real betis"),
    "chelsea": ("chelsea",), "liverpool": ("liverpool",),
    "manchester city": ("manchester city", "man city"),
    "manchester united": ("manchester united", "man united"),
    "real madrid": ("real madrid",), "barcelona": ("barcelona", "barca"),
    "atletico madrid": ("atletico madrid", "atletico de madrid"),
    "psg": ("psg", "paris saint germain"), "bayern": ("bayern", "bayern munich"),
    "juventus": ("juventus", "juve"), "milan": ("ac milan", "milan"),
    "inter": ("inter milan", "inter de milan"), "napoli": ("napoli",),
    "roma": ("as roma", "roma"), "flamengo": ("flamengo",),
    "palmeiras": ("palmeiras",), "santos": ("santos",),
    "vinicius": ("vinicius", "vini jr", "vinicius junior"),
    "mbappe": ("mbappe",), "haaland": ("haaland",), "salah": ("salah",),
    "cristiano ronaldo": ("cristiano ronaldo", "cristiano"),
}

_EVENT_CONCEPTS = {
    "RESULTADO_GANO": {"gano", "vencio", "triunfo", "victoria", "beat", "beaten", "won", "derroto", "supero"},
    "RESULTADO_GOLEADA": {"goleo", "goleada", "pulveriza", "aplasto", "thrash", "rout", "hammered"},
    "RESULTADO_EMPATE": {"empato", "empate", "draw", "drew"},
    "MERCADO": {"fichaje", "refuerzo", "contrato", "negocia", "interes", "oferta", "transfer", "signing", "rumor"},
    "LESION": {"lesion", "baja", "diagnostico", "operacion", "cirugia", "injury", "injured", "out"},
    "SANCION": {"sancion", "suspendido", "expulsion", "ban", "banned", "suspension"},
    "PROGRAMACION": {"fecha", "horario", "sede", "estadio", "postergado", "suspendido", "schedule", "venue"},
    "CONVOCATORIA": {"convocados", "convocado", "lista", "nomina", "squad", "call up"},
    "FORMACION": {"formacion", "titular", "once", "lineup", "starting"},
    "DECLARACION": {"dijo", "declaro", "aseguro", "hablo", "said", "claims"},
    "TITULO": {"campeon", "titulo", "final", "ascenso", "descenso", "champion", "promotion", "relegation"},
}


def normalize_coverage_status(value: str) -> str:
    raw = str(value or "").strip().upper().replace(" ", "_")
    return COVERAGE_ALIASES.get(raw, raw)


def _tokens(title: str) -> set[str]:
    return {
        token for token in normalize_text(title).split()
        if len(token) >= 3 and not token.isdigit()
    }


def _distinctive(title: str) -> set[str]:
    return _tokens(title) - GENERIC_WORDS


def _known_entities(title: str) -> set[str]:
    normalized = f" {normalize_text(title)} "
    entities: set[str] = set()
    try:
        from monitor_core import detectar_entidades
        entities.update(normalize_text(item) for item in detectar_entidades(title))
    except Exception:
        pass
    for canonical, aliases in _ENTITY_ALIASES.items():
        if any(f" {normalize_text(alias)} " in normalized for alias in aliases):
            entities.add(canonical)
    return entities


def _event_concepts(title: str) -> set[str]:
    tokens = _tokens(title)
    normalized = normalize_text(title)
    out: set[str] = set()
    for concept, hints in _EVENT_CONCEPTS.items():
        if any((hint in tokens) if " " not in hint else (hint in normalized) for hint in hints):
            out.add(concept)
    return out


def _similarity_details(source: str, candidate: str) -> dict[str, Any]:
    source_tokens = _distinctive(source)
    candidate_tokens = _distinctive(candidate)
    shared_tokens = source_tokens & candidate_tokens
    union = source_tokens | candidate_tokens
    jaccard = len(shared_tokens) / len(union) if union else 0.0
    containment = len(shared_tokens) / min(len(source_tokens), len(candidate_tokens)) if source_tokens and candidate_tokens else 0.0
    source_entities = _known_entities(source)
    candidate_entities = _known_entities(candidate)
    shared_entities = source_entities & candidate_entities
    shared_events = _event_concepts(source) & _event_concepts(candidate)
    exact = normalize_text(source) == normalize_text(candidate)

    valid = exact
    valid = valid or (len(shared_tokens) >= 4 and containment >= 0.50)
    valid = valid or (len(shared_entities) >= 2 and (len(shared_tokens) >= 2 or bool(shared_events)))
    valid = valid or (len(shared_entities) >= 1 and len(shared_tokens) >= 3 and bool(shared_events))
    valid = valid or (not source_entities and not candidate_entities and len(shared_tokens) >= 5 and containment >= 0.60)

    score = (
        containment * 0.43
        + jaccard * 0.22
        + min(0.24, len(shared_entities) * 0.12)
        + min(0.16, len(shared_events) * 0.08)
    )
    if exact:
        score = 1.0
    elif not valid:
        score = min(score, 0.29)
    return {
        "score": min(1.0, score),
        "valid": valid,
        "shared_tokens": sorted(shared_tokens),
        "shared_entities": sorted(shared_entities),
        "shared_events": sorted(shared_events),
        "containment": containment,
        "jaccard": jaccard,
    }


def normalize_ole_items(items: list[dict] | None) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for item in items or []:
        title = str(item.get("titulo") or item.get("title") or "").strip()
        if len(title) < 8:
            continue
        key = normalize_text(title)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({
            "title": title,
            "url": str(item.get("url_final") or item.get("URLFinal") or item.get("url") or ""),
            "published_at": str(item.get("fecha_publicacion") or item.get("fecha") or ""),
            "summary": str(item.get("bajada") or item.get("summary") or ""),
        })
    return out


def best_ole_match(title: str, ole_items: list[dict]) -> dict:
    best: dict[str, Any] = {
        "score": 0.0, "title": "", "url": "", "shared": [], "valid": False,
        "shared_entities": [], "shared_events": [],
    }
    for item in ole_items:
        candidate_title = str(item.get("title") or "")
        candidate_text = f"{candidate_title}. {item.get('summary', '')}".strip()
        details = _similarity_details(title, candidate_text)
        if details["score"] > best["score"]:
            best = {
                "score": details["score"],
                "title": candidate_title,
                "url": item.get("url", ""),
                "shared": details["shared_tokens"],
                "valid": details["valid"],
                "shared_entities": details["shared_entities"],
                "shared_events": details["shared_events"],
            }
    # Una coincidencia inválida no se muestra como nota relacionada. Esto evita
    # que el editor vea un enlace engañoso por compartir un solo club o apellido.
    if not best.get("valid"):
        return {
            **best,
            "score": min(float(best.get("score", 0) or 0), 0.29),
            "title": "",
            "url": "",
        }
    return best


def _new_detail_tokens(external_titles: list[str], ole_title: str) -> list[str]:
    if not ole_title:
        return []
    ole = _distinctive(ole_title)
    candidates: list[str] = []
    for title in external_titles:
        for token in _distinctive(title) - ole:
            if token in STATUS_WORDS:
                candidates.append(token)
            elif token.isdigit():
                number = int(token)
                # Marcadores 0/1/2 y años no son, por sí solos, un dato nuevo
                # suficiente para pedir una actualización.
                if number > 2 and not (1900 <= number <= 2100):
                    candidates.append(token)
    return unique_strings(candidates)[:8]


def _direct_ole_items(theme: dict) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for item in theme.get("noticias", []) or []:
        news = item.get("noticia", {}) if isinstance(item, dict) else {}
        source = item.get("fuente", {}) if isinstance(item, dict) else {}
        identity = normalize_text(
            f"{news.get('source_id', '')} {news.get('publisher_original', '')} "
            f"{source.get('id', '')} {source.get('nombre', '')}"
        )
        if identity == "ole" or " ole " in f" {identity} ":
            title = str(news.get("titulo") or news.get("title") or "").strip()
            url = str(news.get("url_final") or news.get("URLFinal") or news.get("url") or "").strip()
            key = url or normalize_text(title)
            if title and key not in seen:
                seen.add(key)
                out.append({
                    "title": title,
                    "url": url,
                    "published_at": str(news.get("fecha_publicacion_verificada") or news.get("fecha_publicacion") or ""),
                    "updated_at": str(news.get("fecha_actualizacion") or ""),
                })
    return out


def _direct_ole_evidence(theme: dict) -> bool:
    return bool(_direct_ole_items(theme))


def enrich_theme_coverage(theme: dict, ole_items: list[dict]) -> dict:
    enriched = dict(theme)
    source_titles = [
        str((item.get("noticia") or {}).get("titulo") or "")
        for item in theme.get("noticias", []) or []
        if isinstance(item, dict)
    ]
    representative = str(theme.get("titulo") or "")
    matches = [best_ole_match(title, ole_items) for title in [representative, *source_titles] if title]
    match = max(matches, key=lambda item: float(item.get("score", 0) or 0), default={"score": 0.0, "valid": False})
    direct_items = _direct_ole_items(theme)
    direct = bool(direct_items)
    if direct_items:
        # La evidencia contenida en el propio cluster tiene prioridad absoluta
        # sobre un matching aproximado contra el inventario de Olé. Evita tanto
        # falsos NO_CUBIERTO como enlaces a una nota ajena.
        direct_matches = []
        for item in direct_items:
            details = _similarity_details(representative, item.get("title", ""))
            direct_matches.append({
                "score": max(0.72, float(details.get("score", 0) or 0)),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "shared": details.get("shared_tokens", []),
                "valid": True,
                "shared_entities": details.get("shared_entities", []),
                "shared_events": details.get("shared_events", []),
            })
        match = max(direct_matches, key=lambda item: float(item.get("score", 0) or 0))
    score = float(match.get("score", 0) or 0)
    valid = bool(match.get("valid")) or direct
    non_ole_titles = []
    direct_titles = {normalize_text(item.get("title", "")) for item in direct_items}
    for title in source_titles or [representative]:
        if normalize_text(title) not in direct_titles:
            non_ole_titles.append(title)
    new_details = _new_detail_tokens(non_ole_titles, str(match.get("title") or "")) if valid else []

    if direct and new_details:
        status = "CUBIERTO_CON_DATO_NUEVO"
    elif direct:
        status = "YA_CUBIERTO"
    elif valid and score >= 0.72 and new_details:
        status = "CUBIERTO_CON_DATO_NUEVO"
    elif valid and score >= 0.72:
        status = "YA_CUBIERTO"
    elif valid and score >= 0.55:
        status = "CUBIERTO_CON_DATO_NUEVO" if new_details else "CUBIERTO_PARCIALMENTE"
    elif valid and score >= 0.38:
        status = "COINCIDENCIA_DUDOSA"
    else:
        status = "NO_CUBIERTO"

    enriched.update({
        "coverage_status": status,
        "ole_match_score": round(score, 3),
        "ole_match_title": match.get("title", "") if valid else "",
        "ole_match_url": match.get("url", "") if valid else "",
        "ole_match_entities": match.get("shared_entities", []) if valid else [],
        "ole_match_events": match.get("shared_events", []) if valid else [],
        "new_detail_tokens": new_details,
        "tiene_ole": status in {"YA_CUBIERTO", "CUBIERTO_PARCIALMENTE", "CUBIERTO_CON_DATO_NUEVO"},
    })
    return enriched


def enrich_themes(themes: list[dict], ole_items: list[dict] | None) -> list[dict]:
    normalized = normalize_ole_items(ole_items)
    return [enrich_theme_coverage(theme, normalized) for theme in themes or []]
