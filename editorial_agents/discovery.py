from __future__ import annotations

import os
from datetime import datetime, timezone

from .coverage import best_ole_match, normalize_ole_items
from .utils import clamp, normalize_text, stable_id, unique_strings

RARE_HINTS = {
    "insolito", "insolita", "bizarre", "weird", "strange", "unusual", "curious",
    "record", "historico", "historic", "historia", "primera vez", "youngest", "oldest",
    "milagro", "miracle", "escandalo", "scandal", "gol de arquero", "goalkeeper scores",
    "own goal", "autogol", "comeback", "remontada", "inusitado", "curioso", "recorde",
    "goleiro marcou", "virada", "insolite", "gardien buteur", "kurios", "torwart tor",
}
VISUAL_HINTS = {
    "video", "imagen", "foto", "viral", "camara", "camera", "celebracion", "celebration",
    "hinchas", "fans", "torcida", "tifosi", "supporters", "estadio", "stadium", "golazo",
    "blooper", "viralizou", "virale",
}
DATA_HINTS = {
    "record", "recorde", "rekord", "historico", "historic", "historique", "storico",
    "primera vez", "youngest", "oldest", "racha", "estadistica", "stat", "million",
    "millones", "ranking", "marca",
}
HUMAN_HINTS = {
    "historia humana", "familia", "madre", "padre", "hijo", "hija", "superacion",
    "refugiado", "hospital", "cancer", "discapacidad", "emocion", "tears", "llanto",
    "wedding", "casamiento", "homenaje", "tribute",
}
CONFLICT_HINTS = {
    "conflicto", "pelea", "denuncia", "tribunal", "court", "ban", "sancion", "expulso",
    "escandalo", "scandal", "polémica", "polemica", "protesta", "boicot", "desmentido",
}
BUSINESS_TECH_HINTS = {
    "tecnologia", "technology", "inteligencia artificial", "robot", "negocio", "business",
    "inversion", "venta", "compra", "millones", "salario", "premio", "derechos", "streaming",
    "estadio inteligente", "biometria", "ticketing",
}
CONSEQUENCE_HINTS = {
    "ascenso", "descenso", "clasifico", "eliminado", "campeon", "final", "titulo", "promotion",
    "relegation", "qualified", "knocked out", "champion", "suspendido", "sancion", "baja",
}
ROUTINE_HINTS = {
    "probable formacion", "probable lineup", "training", "entrenamiento", "practica", "preview",
    "previa", "where to watch", "donde ver", "hora y tv", "convocados", "said", "dijo",
    "hablo", "declaracion", "press conference", "conferencia", "rumor", "could sign",
    "interested in", "sondeo", "interesa", "negocia", "mercato", "calciomercato",
}
ARGENTINA_HINTS = {
    "argentin", "messi", "scaloni", "dibu", "emiliano martinez", "julian alvarez", "lautaro",
    "enzo fernandez", "mac allister", "cuti romero", "garnacho", "mastantuono", "nico paz",
    "di maria", "de paul", "otamendi", "simeone", "bielsa", "pochettino", "gallardo",
    "river", "boca", "racing", "independiente", "san lorenzo", "libertadores", "sudamericana",
}
GLOBAL_HINTS = {
    "real madrid", "barcelona", "manchester", "liverpool", "arsenal", "chelsea", "psg",
    "bayern", "juventus", "milan", "inter", "champions", "world cup", "mundial",
    "premier league", "la liga", "serie a", "formula 1", "nba", "mbappe", "haaland",
    "cristiano", "neymar", "vinicius", "lamine yamal",
}
QUALITY_SOURCE_IDS = {
    "bbc", "guardian", "reuters_dep", "efe", "afp_f24", "fifa", "uefa", "conmebol",
    "athletic", "lequipe", "gazzetta", "globo", "geglobo", "skysports", "kicker",
    "sportspro", "frontoffice", "olympics",
}


def _parse_date(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _jaccard(a: str, b: str) -> float:
    stop = {"the", "and", "for", "with", "from", "after", "ante", "para", "tras", "sobre", "club"}
    ta = {x for x in normalize_text(a).split() if len(x) >= 3 and x not in stop}
    tb = {x for x in normalize_text(b).split() if len(x) >= 3 and x not in stop}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _category(signals: list[str], arg_hook: bool) -> str:
    if arg_hook:
        return "CONEXION ARGENTINA"
    if "VISUAL" in signals:
        return "OPORTUNIDAD VISUAL"
    if "DATO O RECORD" in signals:
        return "DATO O RECORD"
    if "NEGOCIO O TECNOLOGIA" in signals:
        return "NEGOCIO / TECNOLOGIA"
    if "HISTORIA HUMANA" in signals:
        return "HISTORIA HUMANA"
    if "RAREZA" in signals:
        return "HISTORIA RARA"
    return "RADAR INTERNACIONAL"


def _signals(text: str) -> tuple[list[str], bool, bool, bool]:
    arg_hook = any(h in text for h in ARGENTINA_HINTS)
    global_hook = any(h in text for h in GLOBAL_HINTS)
    routine = any(h in text for h in ROUTINE_HINTS)
    values: list[str] = []
    if arg_hook:
        values.append("CONEXION ARGENTINA")
    if any(h in text for h in RARE_HINTS):
        values.append("RAREZA")
    if any(h in text for h in VISUAL_HINTS):
        values.append("VISUAL")
    if any(h in text for h in DATA_HINTS):
        values.append("DATO O RECORD")
    if any(h in text for h in HUMAN_HINTS):
        values.append("HISTORIA HUMANA")
    if any(h in text for h in CONFLICT_HINTS):
        values.append("CONFLICTO")
    if any(h in text for h in BUSINESS_TECH_HINTS):
        values.append("NEGOCIO O TECNOLOGIA")
    if any(h in text for h in CONSEQUENCE_HINTS):
        values.append("CONSECUENCIA DEPORTIVA")
    if global_hook:
        values.append("ALCANCE GLOBAL")
    return unique_strings(values), arg_hook, global_hook, routine


def _editorial_score(title: str, media_count: int, age_hours: float | None,
                     ole_score: float) -> tuple[int, int, list[str], str]:
    text = normalize_text(title)
    signals, arg_hook, global_hook, routine = _signals(text)
    signal_weights = {
        "CONEXION ARGENTINA": 24, "RAREZA": 18, "VISUAL": 10, "DATO O RECORD": 10,
        "HISTORIA HUMANA": 12, "CONFLICTO": 10, "NEGOCIO O TECNOLOGIA": 11,
        "CONSECUENCIA DEPORTIVA": 14, "ALCANCE GLOBAL": 8,
    }
    score = 14 + sum(signal_weights.get(signal, 0) for signal in signals)
    score += min(10, max(0, media_count - 1) * 3)
    score -= 18 if routine and len(signals) < 2 and not arg_hook else 0
    score -= 30 if ole_score >= 0.68 else (14 if ole_score >= 0.48 else 0)
    if age_hours is None:
        score -= 20
    elif age_hours <= 2:
        score += 9
    elif age_hours <= 6:
        score += 4
    elif age_hours > 12:
        score -= 24
    score = clamp(score)

    value_ar = 12 + (42 if arg_hook else 0) + (18 if global_hook else 0)
    value_ar += min(24, len(signals) * 5)
    value_ar = clamp(value_ar)
    return score, value_ar, signals, _category(signals, arg_hook)


def _confidence(source_ids: list[str], publishers: list[str], date_trust: str) -> tuple[int, str]:
    direct = str(date_trust or "").lower() not in {"discovery_timestamp", "missing", "unverified"}
    quality_count = sum(1 for source_id in source_ids if source_id in QUALITY_SOURCE_IDS)
    score = 34 + (24 if direct else -20)
    score += min(24, max(0, len(publishers) - 1) * 8)
    score += min(18, quality_count * 9)
    score = clamp(score)
    reasons = []
    reasons.append("fecha directa del publisher" if direct else "fecha no verificada")
    if len(publishers) > 1:
        reasons.append(f"{len(publishers)} publishers originales")
    if quality_count:
        reasons.append(f"{quality_count} fuente(s) de alta confianza")
    return score, "; ".join(reasons)


def _status(score: int, confidence: int, signal_count: int, strong_threshold: int) -> str:
    if score >= strong_threshold and confidence >= 60 and signal_count >= 3:
        return "HALLAZGO FUERTE"
    if score >= max(46, strong_threshold - 16) and confidence >= 50 and signal_count >= 2:
        return "HALLAZGO"
    return "CANDIDATO PARA EXPLORAR"


def _international_source_ids(source_map: dict) -> set[str]:
    try:
        from monitor_core import FUENTES_NAC_IDS, FUENTES_ESP_IDS
        return set(source_map) - set(FUENTES_NAC_IDS) - set(FUENTES_ESP_IDS)
    except Exception:
        return set(source_map)


def _collect(results: dict, source_map: dict, max_age_hours: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    allowed = _international_source_ids(source_map)
    items: list[dict] = []
    for source_id, news_items in (results or {}).items():
        if allowed and source_id not in allowed:
            continue
        source = source_map.get(source_id, {"id": source_id, "nombre": source_id})
        for news in news_items or []:
            title = str(news.get("titulo") or "").strip()
            if len(title) < 18:
                continue
            published = _parse_date(news.get("fecha_publicacion", ""))
            source_url = str(source.get("url") or "")
            channel = str(news.get("discovery_channel") or "")
            trust = str(news.get("date_trust") or "")
            if not trust:
                is_gnews = channel.lower() == "google news" or "news.google.com" in source_url or source_id.startswith("gn_")
                trust = "discovery_timestamp" if is_gnews else "publisher_timestamp"
            if published is None or trust in {"discovery_timestamp", "missing", "unverified"}:
                continue
            age = max(0.0, (now - published).total_seconds() / 3600)
            if age > max_age_hours:
                continue
            items.append({
                "source_id": source_id,
                "source_name": source.get("nombre", source_id),
                "publisher": news.get("publisher_original") or source.get("nombre", source_id),
                "title": title,
                "url": news.get("url", ""),
                "published_at": news.get("fecha_publicacion", ""),
                "age_hours": age,
                "date_trust": trust,
            })
    return items


def _cluster(items: list[dict]) -> list[list[dict]]:
    clusters: list[list[dict]] = []
    for item in items:
        best_index = None
        best_score = 0.0
        for index, cluster in enumerate(clusters):
            score = max(_jaccard(item["title"], member["title"]) for member in cluster)
            if score > best_score:
                best_score, best_index = score, index
        if best_index is not None and best_score >= 0.32:
            clusters[best_index].append(item)
        else:
            clusters.append([item])
    return clusters


def generate(results: dict, ole_items: list[dict] | None, previous: list[dict] | None = None,
             max_items: int = 12, config: dict | None = None) -> list[dict]:
    config = config or {}
    max_age_hours = int(config.get("discovery_max_age_hours") or os.environ.get("DISCOVERY_MAX_AGE_HOURS", "12") or 12)
    strong_threshold = int(os.environ.get("DISCOVERY_MIN_SCORE", "62") or 62)
    try:
        from monitor_core import TODAS_FUENTES
        source_map = {source["id"]: source for source in TODAS_FUENTES}
    except Exception:
        source_map = {}

    normalized_ole = normalize_ole_items(ole_items)
    prev_by_id = {
        str(row.get("DiscoveryID") or row.get("discovery_id") or ""): row
        for row in previous or [] if str(row.get("DiscoveryID") or row.get("discovery_id") or "")
    }
    discoveries: list[dict] = []
    for cluster in _cluster(_collect(results, source_map, max_age_hours)):
        representative = min(cluster, key=lambda x: x.get("age_hours") if x.get("age_hours") is not None else 999)
        publishers = unique_strings([item.get("publisher", "") for item in cluster])
        source_ids = unique_strings([item.get("source_id", "") for item in cluster])
        match = best_ole_match(representative["title"], normalized_ole)
        score, value_ar, signals, category = _editorial_score(
            representative["title"], len(publishers), representative.get("age_hours"), float(match.get("score", 0) or 0)
        )
        confidence, confidence_reason = _confidence(source_ids, publishers, representative.get("date_trust", ""))
        discovery_id = stable_id(normalize_text(representative["title"]), "d")
        previous_item = prev_by_id.get(discovery_id)
        is_new = previous_item is None
        try:
            previous_media = int(float(previous_item.get("Medios", 0))) if previous_item else 0
        except Exception:
            previous_media = 0
        grew = bool(previous_item) and len(publishers) > previous_media
        if previous_item and not grew:
            score = max(0, score - 8)
        status = _status(score, confidence, len(signals), strong_threshold)

        editorial_reasons = [signal.lower() for signal in signals]
        if float(match.get("score", 0) or 0) < 0.30:
            editorial_reasons.append("no se encontró una pieza equivalente en Olé")
        elif float(match.get("score", 0) or 0) < 0.68:
            editorial_reasons.append("la coincidencia con Olé es parcial")
        if representative.get("age_hours") is not None:
            editorial_reasons.append(f"publicada hace {representative['age_hours']:.1f} horas")
        if previous_item and not grew:
            editorial_reasons.append("ya apareció en el corte anterior sin crecimiento")
        elif grew:
            editorial_reasons.append(f"sumó {len(publishers) - previous_media} publisher(s)")

        why = _why_it_matters(signals, representative["title"])
        discoveries.append({
            "discovery_id": discovery_id,
            "title": representative["title"],
            "url": representative.get("url", ""),
            "category": category,
            "status": status,
            "score": score,
            "noticiability": score,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "signals": signals,
            "signal_count": len(signals),
            "value_argentina": value_ar,
            "publishers": publishers,
            "media_count": len(publishers),
            "published_at": representative.get("published_at", ""),
            "age_hours": representative.get("age_hours"),
            "date_trust": representative.get("date_trust", "publisher_timestamp"),
            "is_new": is_new,
            "grew": grew,
            "ole_status": "NO_CUBIERTO" if float(match.get("score", 0) or 0) < 0.30 else "COINCIDENCIA_DUDOSA",
            "ole_match_title": match.get("title", ""),
            "ole_match_url": match.get("url", ""),
            "reason": ". ".join(unique_strings(editorial_reasons)),
            "why_it_matters": why,
            "suggested_angle": _suggest_angle(category, representative["title"]),
            "suggested_format": _suggest_format(category),
            "evidence": cluster[:8],
            "notify": (is_new or grew) and status == "HALLAZGO FUERTE",
        })

    rank = {"HALLAZGO FUERTE": 0, "HALLAZGO": 1, "CANDIDATO PARA EXPLORAR": 2}
    discoveries.sort(key=lambda item: (rank.get(item["status"], 3), -item["score"], -item["confidence"], item.get("age_hours") or 999))
    return discoveries[:max_items]


def _why_it_matters(signals: list[str], title: str) -> str:
    if "CONEXION ARGENTINA" in signals:
        return "Tiene una conexión directa con protagonistas, clubes o competencias de interés para el lector argentino."
    if "CONSECUENCIA DEPORTIVA" in signals:
        return "El desenlace cambia una clasificación, un ascenso, un descenso o una definición deportiva."
    if "RAREZA" in signals and "VISUAL" in signals:
        return "Combina un hecho extraordinario con una escena o video de alto potencial editorial."
    if "NEGOCIO O TECNOLOGIA" in signals:
        return "Permite explicar una tendencia de negocio o tecnología deportiva poco cubierta en Argentina."
    if "HISTORIA HUMANA" in signals:
        return "Tiene un protagonista y una dimensión humana que puede trascender el resultado."
    return f"Es un tema internacional para evaluar por su novedad y posible enfoque local: {title[:140]}."


def _suggest_angle(category: str, title: str) -> str:
    if category == "CONEXION ARGENTINA":
        return "Explicar por qué la historia importa en Argentina y cuál es el vínculo local concreto."
    if category == "OPORTUNIDAD VISUAL":
        return "Contar el hecho desde la escena o el video y sumar el contexto que la vuelve significativa."
    if category == "DATO O RECORD":
        return "Poner el dato en perspectiva con antecedentes y comparación."
    if category == "HISTORIA RARA":
        return "Convertir la rareza en una historia con personaje, giro y consecuencia."
    if category == "NEGOCIO / TECNOLOGIA":
        return "Explicar el impacto deportivo, económico y práctico de la innovación."
    return "Buscar el ángulo que vuelva relevante esta noticia para el lector deportivo argentino."


def _suggest_format(category: str) -> str:
    return {
        "CONEXION ARGENTINA": "PERFIL / EXPLICADOR",
        "OPORTUNIDAD VISUAL": "NOTA BREVE + VIDEO",
        "DATO O RECORD": "DATOS / COMPARATIVA",
        "HISTORIA RARA": "HISTORIA / COLOR",
        "HISTORIA HUMANA": "PERFIL / HISTORIA",
        "NEGOCIO / TECNOLOGIA": "EXPLICADOR",
        "RADAR INTERNACIONAL": "EXPLORACION / SEGUIMIENTO",
    }.get(category, "HISTORIA")
