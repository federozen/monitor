from __future__ import annotations

"""Consolidación determinística de clusters que describen el mismo hecho.

El recolector histórico agrupa por similitud de títulos. Eso funciona para
copias casi literales, pero tiende a separar una historia viva en varios
clusters cuando cambia el enfoque (resultado, gol, análisis, declaraciones).
Este módulo hace una segunda pasada conservadora antes del análisis editorial.
"""

import re
from collections import Counter
from typing import Any

from .utils import normalize_text, unique_strings

_GENERIC = {
    "partido", "torneo", "fecha", "resultado", "vivo", "minuto", "hora",
    "como", "donde", "ver", "equipo", "futbol", "club", "primero", "primera",
    "nuevo", "nueva", "ultimo", "ultima", "tras", "ante", "para", "sobre",
    "ganó", "gano", "venció", "vencio", "empató", "empato", "perdió", "perdio",
    "gol", "video", "duelo", "juego", "jornada", "liga", "copa", "clausura",
}

# Complementa detectar_entidades con nombres que suelen aparecer en títulos
# pero no siempre están presentes en el diccionario heredado.
_ENTITY_ALIASES = {
    "boca": ("boca", "boca juniors"),
    "river": ("river", "river plate"),
    "estudiantes": ("estudiantes", "estudiantes de la plata"),
    "tigre": ("tigre",),
    "belgrano": ("belgrano",),
    "racing": ("racing",),
    "independiente": ("independiente",),
    "san lorenzo": ("san lorenzo",),
    "inter miami": ("inter miami",),
    "atletico san luis": ("atletico san luis", "san luis"),
    "messi": ("messi", "lionel messi"),
    "ascacibar": ("ascacibar", "ascacíbar"),
    "arsenal": ("arsenal",),
    "betis": ("betis", "real betis"),
    "lisandro martinez": ("lisandro martinez", "licha martinez"),
    "colapinto": ("colapinto", "franco colapinto"),
}

_EVENT_GROUPS = {
    "MATCH_RESULT": {
        "gano", "vencio", "derroto", "triunfo", "victoria", "empato", "empate",
        "perdio", "resultado", "gol", "doblete", "asistencia", "uno por uno",
        "puntajes", "highlights", "resumen", "marcador", "clasifico", "elimino",
    },
    "MATCH_SERVICE": {
        "hora", "tv", "formaciones", "como ver", "en vivo", "minuto a minuto",
        "previa", "alineaciones", "probables", "partido pendiente",
    },
    "MARKET": {
        "fichaje", "refuerzo", "mercado", "oferta", "contrato", "venta", "compra",
        "prestamo", "cesion", "negocia", "interes", "salida", "llegada",
    },
    "INJURY": {
        "lesion", "baja", "parte medico", "diagnostico", "operacion", "cirugia",
        "recuperacion", "dolor", "molestia",
    },
    "SCHEDULE": {
        "fecha", "horario", "sede", "estadio", "programacion", "postergado",
        "suspendido", "reprogramado",
    },
    "STATEMENT": {
        "dijo", "declaro", "hablo", "aseguro", "mensaje", "conferencia", "elogios",
    },
}


def _title(cluster: dict) -> str:
    return str(cluster.get("titulo") or cluster.get("title") or "").strip()


def _source_titles(cluster: dict) -> list[str]:
    titles = [_title(cluster)]
    for item in cluster.get("noticias", []) or []:
        if not isinstance(item, dict):
            continue
        news = item.get("noticia") if isinstance(item.get("noticia"), dict) else item
        title = str(news.get("titulo") or news.get("title") or "").strip()
        if title:
            titles.append(title)
    return unique_strings(titles)


def _tokens(titles: list[str]) -> set[str]:
    out: set[str] = set()
    for title in titles:
        out.update(
            token for token in normalize_text(title).split()
            if len(token) >= 3 and token not in _GENERIC
        )
    return out


def _entities_for_title(title: str) -> set[str]:
    out: set[str] = set()
    try:
        from monitor_core import detectar_entidades
        out.update(normalize_text(value) for value in detectar_entidades(title) or [])
    except Exception:
        pass
    text = f" {normalize_text(title)} "
    for canonical, aliases in _ENTITY_ALIASES.items():
        if any(f" {normalize_text(alias)} " in text for alias in aliases):
            out.add(canonical)
    # Competencias y categorías amplias no identifican por sí solas una
    # historia. Mantenerlas provocaba puentes falsos entre AFA, Messi y Mundial.
    broad = {"mundial", "argentina", "seleccion", "futbol", "torneo", "liga", "copa"}
    return {entity for entity in out if entity not in broad}


def _entities(titles: list[str]) -> set[str]:
    if not titles:
        return set()
    representative = _entities_for_title(titles[0])
    counts: Counter[str] = Counter()
    for title in titles:
        counts.update(_entities_for_title(title))
    return representative | {entity for entity, count in counts.items() if count >= 2}

def _events(titles: list[str]) -> set[str]:
    text = " ".join(normalize_text(title) for title in titles)
    words = set(text.split())
    out: set[str] = set()
    for group, hints in _EVENT_GROUPS.items():
        if any((hint in words) if " " not in hint else (hint in text) for hint in hints):
            out.add(group)
    return out


def _fingerprint(cluster: dict) -> dict[str, Any]:
    titles = _source_titles(cluster)
    representative_tokens = _tokens(titles[:1])
    token_counts: Counter[str] = Counter()
    for title in titles:
        token_counts.update(_tokens([title]))
    stable_tokens = representative_tokens | {token for token, count in token_counts.items() if count >= 2}
    return {
        "titles": titles,
        "tokens": stable_tokens,
        "entities": _entities(titles),
        "events": _events(titles[:1]) | {event for event in _events(titles) if event in _events(titles[:1])},
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _compatible(a: dict, b: dict) -> bool:
    shared_entities = a["entities"] & b["entities"]
    shared_events = a["events"] & b["events"]
    token_jaccard = _jaccard(a["tokens"], b["tokens"])
    shared_tokens = a["tokens"] & b["tokens"]

    # Dos equipos/protagonistas y el mismo tipo de hecho: caso típico de un
    # partido contado como resultado, gol, puntajes o análisis.
    if len(shared_entities) >= 2 and (shared_events or len(shared_tokens) >= 2):
        return True

    # Un único protagonista solo alcanza cuando el vocabulario específico es
    # muy parecido. Así Messi + Inter Miami se une, pero Barcelona + fichaje no
    # mezcla a Julián Álvarez con Kerolin.
    if len(shared_entities) >= 1 and shared_events and len(shared_tokens) >= 4 and token_jaccard >= 0.25:
        return True
    if len(shared_entities) >= 1 and len(shared_tokens) >= 5 and token_jaccard >= 0.30:
        return True

    # Casi duplicados sin depender del diccionario de entidades.
    if token_jaccard >= 0.55 and len(shared_tokens) >= 4:
        return True

    return False


def _trusted_date_count(cluster: dict) -> int:
    untrusted = {"", "missing", "discovery_timestamp", "unverified", "publisher_date_only"}
    count = 0
    for item in cluster.get("noticias", []) or []:
        news = item.get("noticia", {}) if isinstance(item, dict) else {}
        trust = str(news.get("date_trust") or "").lower()
        if trust not in untrusted and (news.get("fecha_publicacion_verificada") or news.get("fecha_publicacion")):
            count += 1
    return count


def _representative_score(cluster: dict) -> tuple[int, int, int, int]:
    title = _title(cluster)
    titles = _source_titles(cluster)
    entities = _entities(titles)
    bad_prefix = bool(re.match(r"^(detalles|pura energia|proyecto oficialista|en vivo)\s*[.:]", normalize_text(title)))
    direct = 0
    for item in cluster.get("noticias", []) or []:
        news = item.get("noticia", {}) if isinstance(item, dict) else {}
        if str(news.get("discovery_channel") or "").lower() != "google news":
            direct += 1
    return (
        int(cluster.get("cant_medios") or 0),
        _trusted_date_count(cluster) + direct,
        len(entities),
        -int(bad_prefix),
    )


def _merge_group(group: list[dict]) -> dict:
    representative = max(group, key=_representative_score)
    merged = dict(representative)
    news: list[dict] = []
    seen_news: set[str] = set()
    source_ids: set[str] = set()
    publisher_names: set[str] = set()
    publisher_zones: dict[str, str] = {}

    for cluster in group:
        source_ids.update(cluster.get("fuente_ids") or [])
        for name in cluster.get("medios_originales") or []:
            publisher_names.add(str(name))
        for item in cluster.get("noticias", []) or []:
            if not isinstance(item, dict):
                continue
            raw_news = item.get("noticia") if isinstance(item.get("noticia"), dict) else item
            source = item.get("fuente") if isinstance(item.get("fuente"), dict) else {}
            key = str(raw_news.get("url_final") or raw_news.get("url") or normalize_text(str(raw_news.get("titulo") or "")))
            if key and key in seen_news:
                continue
            if key:
                seen_news.add(key)
            news.append(item)
            source_id = str(raw_news.get("source_id") or source.get("id") or "")
            if source_id:
                source_ids.add(source_id)
            publisher = str(raw_news.get("publisher_original") or source.get("nombre") or source_id or "").strip()
            if publisher:
                publisher_names.add(publisher)
            zone = "nac" if source_id in _national_source_ids() else "intl"
            if publisher:
                publisher_zones.setdefault(normalize_text(publisher), zone)

    merged["noticias"] = news
    merged["fuente_ids"] = sorted(source_ids)
    merged["medios_originales"] = sorted(publisher_names, key=str.lower)
    merged["cant_medios"] = len({normalize_text(name) for name in publisher_names if name})
    merged["nac"] = sum(1 for zone in publisher_zones.values() if zone == "nac")
    merged["intl"] = sum(1 for zone in publisher_zones.values() if zone == "intl")
    merged["tiene_ole"] = any(normalize_text(name) == "ole" for name in publisher_names) or "ole" in source_ids
    merged["_merged_cluster_count"] = len(group)
    merged["_merged_titles"] = unique_strings([_title(item) for item in group])
    return merged


def _national_source_ids() -> set[str]:
    try:
        from monitor_core import FUENTES_NAC_IDS
        return set(FUENTES_NAC_IDS)
    except Exception:
        return set()


def consolidate_stories(clusters: list[dict]) -> list[dict]:
    """Fusiona solo pares con evidencia fuerte de pertenecer al mismo hecho.

    Usa agrupación por ancla, no clausura transitiva: una coincidencia débil no
    puede actuar como puente para arrastrar una tercera historia diferente.
    """
    clusters = list(clusters or [])
    if len(clusters) < 2:
        return clusters
    ordered = sorted(clusters, key=_representative_score, reverse=True)
    groups: list[dict[str, Any]] = []
    for cluster in ordered:
        fingerprint = _fingerprint(cluster)
        best_group = None
        best_score = -1.0
        for group in groups:
            anchor = group["anchor"]
            if not _compatible(fingerprint, anchor):
                continue
            # Además del ancla, debe coincidir con al menos la mitad de los
            # miembros ya agrupados para impedir encadenamientos accidentales.
            compatible_members = sum(1 for member_fp in group["fingerprints"] if _compatible(fingerprint, member_fp))
            if compatible_members < max(1, (len(group["fingerprints"]) + 1) // 2):
                continue
            score = len(fingerprint["entities"] & anchor["entities"]) * 2 + len(fingerprint["tokens"] & anchor["tokens"])
            if score > best_score:
                best_group, best_score = group, score
        if best_group is None:
            groups.append({"anchor": fingerprint, "fingerprints": [fingerprint], "clusters": [cluster]})
        else:
            best_group["clusters"].append(cluster)
            best_group["fingerprints"].append(fingerprint)

    merged = [_merge_group(group["clusters"]) if len(group["clusters"]) > 1 else group["clusters"][0] for group in groups]
    merged.sort(key=lambda row: (-int(row.get("cant_medios") or 0), -len(row.get("noticias") or []), _title(row)))
    return merged
