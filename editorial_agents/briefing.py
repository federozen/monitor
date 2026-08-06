from __future__ import annotations

import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

from .coverage import normalize_coverage_status
from .utils import canonical_cluster_id, normalize_text, now_ar, stable_id, unique_strings


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", ".")))
    except Exception:
        return default


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"si", "sí", "true", "1", "yes"}


def _title(row: dict) -> str:
    return str(row.get("titulo") or row.get("Titulo") or row.get("title") or "").strip()


def _url(row: dict) -> str:
    return str(row.get("url") or row.get("URL") or "").strip()


def _media(row: dict) -> int:
    return _int(row.get("cant_medios") or row.get("Medios") or row.get("media_count") or 0)


def _cluster_id(row: dict) -> str:
    return str(row.get("cluster_id") or row.get("ClusterID") or canonical_cluster_id(_title(row)))


def _has_ole(row: dict) -> bool:
    coverage = normalize_coverage_status(str(row.get("coverage_status") or row.get("CoberturaOle") or ""))
    if coverage:
        return coverage in {"YA_CUBIERTO", "CUBIERTO_PARCIALMENTE", "CUBIERTO_CON_DATO_NUEVO"}
    return _bool(row.get("tiene_ole") or row.get("TieneOle"))


def _momentum(row: dict) -> int:
    return _int(row.get("momentum") or row.get("Momentum") or row.get("delta") or 0)


def _action(row: dict) -> str:
    raw = str(row.get("action") or row.get("Accion") or row.get("accion") or "OBSERVAR").upper()
    aliases = {
        "SUBIR YA": "PUBLICAR AHORA",
        "REDACTAR": "PUBLICAR AHORA",
        "RETOMAR": "ACTUALIZAR",
        "EXPLOTA": "ACTUALIZAR",
        "EMPUJAR": "SEGUIR",
        "OBSERVAR": "OBSERVAR",
    }
    return aliases.get(raw, raw)


def _source_titles(row: dict) -> list[str]:
    raw = row.get("noticias") or row.get("Fuentes") or row.get("fuentes") or []
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        news = item.get("noticia") if isinstance(item.get("noticia"), dict) else item
        title = str(news.get("titulo") or news.get("title") or "").strip()
        if title:
            result.append(title)
    return result


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def _best_previous(row: dict, previous: dict[str, dict], used: set[str]) -> tuple[str | None, dict | None]:
    cid = _cluster_id(row)
    if cid in previous and cid not in used:
        return cid, previous[cid]
    best_id = None
    best_row = None
    best_score = 0.0
    for prev_id, prev_row in previous.items():
        if prev_id in used:
            continue
        score = _similarity(_title(row), _title(prev_row))
        if score > best_score:
            best_id, best_row, best_score = prev_id, prev_row, score
    if best_score >= 0.52:
        return best_id, best_row
    return None, None


def _current_map(themes: list[dict]) -> dict[str, dict]:
    return {_cluster_id(row): row for row in themes or [] if _title(row)}


def _previous_map(themes: list[dict]) -> dict[str, dict]:
    return {_cluster_id(row): row for row in themes or [] if _title(row)}


def _recommendation_by_cluster(recommendations: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for rec in recommendations or []:
        cid = str(rec.get("cluster_id") or rec.get("ClusterID") or "").strip()
        if cid:
            result[cid] = rec
    return result


_FACT_GROUPS = {
    "CONFIRMACION": {"oficial", "confirmado", "confirmo", "comunicado", "anuncio", "presentado", "firmo"},
    "DESMENTIDA": {"desmintio", "desmentido", "nego", "falso", "descarto", "contradijo"},
    "PARTE_MEDICO": {"lesion", "lesionado", "baja", "diagnostico", "operado", "cirugia", "recuperacion"},
    "PLAZO": {"dias", "semanas", "meses", "plazo"},
    "CIFRA": {"millones", "euros", "dolares", "monto", "cifra", "salario", "clausula"},
    "PROGRAMACION": {"fecha", "horario", "hora", "sede", "estadio", "postergado", "suspendido"},
    "FORMACION": {"titular", "suplente", "convocados", "formacion", "once", "lista"},
    "SANCION": {"sancion", "suspendido", "expulsado", "inhabilitado", "fallo"},
    "RESULTADO": {"gano", "perdio", "empato", "vencio", "resultado", "clasifico", "eliminado", "campeon", "gol"},
    "MERCADO": {"fichaje", "refuerzo", "pase", "transferencia", "contrato", "acuerdo", "cesion"},
}


def _fact_markers(titles: list[str]) -> set[str]:
    markers: set[str] = set()
    for title in titles:
        text = normalize_text(title)
        words = set(text.split())
        for group, terms in _FACT_GROUPS.items():
            if words & terms:
                markers.add(group)
        # Los números aislados de un marcador (0, 1, 2) o el año de la
        # competencia no constituyen por sí mismos un cambio editorial. Los
        # grupos RESULTADO, CIFRA y PLAZO ya capturan el sentido relevante.
        for match in re.findall(r"\b\d+(?:[.,]\d+)?\b", text):
            normalized_number = match.replace(',', '.')
            try:
                numeric = float(normalized_number)
            except ValueError:
                continue
            if numeric <= 2 or 1900 <= numeric <= 2100:
                continue
            markers.add(f"NUMERO:{normalized_number}")
        for hh, mm in re.findall(r"\b([0-2]?\d)[:.]([0-5]\d)\b", text):
            markers.add(f"HORA:{int(hh):02d}:{mm}")
    return markers


def _marker_label(marker: str) -> str:
    group, _, value = marker.partition(":")
    labels = {
        "CONFIRMACION": "apareció una confirmación oficial",
        "DESMENTIDA": "apareció una desmentida o contradicción",
        "PARTE_MEDICO": "se incorporó información médica",
        "PLAZO": "se agregó un plazo",
        "CIFRA": "se agregó una cifra o monto",
        "PROGRAMACION": "cambió una fecha, horario o sede",
        "FORMACION": "se agregó información de formación o convocatoria",
        "SANCION": "se informó una sanción",
        "RESULTADO": "el hecho pasó a tener resultado o desenlace",
        "MERCADO": "se agregó una novedad de mercado",
        "NUMERO": f"apareció el dato numérico {value}",
        "HORA": f"apareció el horario {value}",
    }
    return labels.get(group, marker)


def _coverage(row: dict, rec: dict | None = None) -> str:
    return normalize_coverage_status(str((rec or {}).get("coverage_status") or row.get("coverage_status") or row.get("CoberturaOle") or ("YA_CUBIERTO" if _has_ole(row) else "NO_CUBIERTO")))


def _delta_description(current: dict, previous: dict | None, rec: dict | None) -> tuple[str, str, int, str, str]:
    current_media = _media(current)
    current_action = str((rec or {}).get("action") or _action(current)).upper()
    current_coverage = _coverage(current, rec)
    current_titles = unique_strings([_title(current), *_source_titles(current)])

    if previous is None:
        if current_coverage == "YA_CUBIERTO":
            return "NUEVO EN EL CORTE", "Apareció por primera vez en el panorama, pero Olé ya tiene cobertura equivalente.", 40, "Sin registro comparable", _title(current)
        return "NUEVO SIN CUBRIR", "Apareció por primera vez en el panorama y no se detectó una cobertura equivalente en Olé.", 82, "Sin registro comparable", _title(current)

    prev_media = _media(previous)
    prev_action = _action(previous)
    prev_coverage = _coverage(previous)
    previous_titles = unique_strings([_title(previous), *_source_titles(previous)])
    new_markers = sorted(_fact_markers(current_titles) - _fact_markers(previous_titles))

    deltas: list[str] = []
    priority = 35
    change_type = "NUEVA INFORMACION"

    if current_coverage != prev_coverage:
        deltas.append(f"la cobertura de Olé pasó de {prev_coverage} a {current_coverage}")
        priority += 16
        change_type = "CAMBIO DE COBERTURA"
    if current_action != prev_action:
        deltas.append(f"la acción sugerida cambió de {prev_action} a {current_action}")
        priority += 14
        change_type = "CAMBIO DE ACCION"
    if new_markers:
        deltas.extend(_marker_label(marker) for marker in new_markers[:5])
        priority += min(35, 8 * len(new_markers))
        change_type = "NUEVO DATO"

    # Más publishers solo acompaña un cambio editorial real; no crea un cambio por sí mismo.
    if current_media > prev_media and deltas:
        deltas.append(f"la evidencia pasó de {prev_media} a {current_media} publishers")
        priority += min(12, (current_media - prev_media) * 3)

    if not deltas:
        return "SIN CAMBIO", "No cambió de forma editorialmente relevante respecto del corte anterior.", 0, _title(previous), _title(current)

    if current_action == "ACTUALIZAR":
        change_type = "ACTUALIZAR NOTA"
        priority = max(priority, 78)
    elif current_action == "VERIFICAR":
        change_type = "VERIFICAR"
        priority = max(priority, 68)
    elif current_action == "PUBLICAR AHORA" and current_coverage == "NO_CUBIERTO":
        change_type = "PUBLICAR"
        priority = max(priority, 82)

    return change_type, "; ".join(deltas) + ".", min(100, priority), _title(previous), _title(current)


def build_changes(current_themes: list[dict], previous_themes: list[dict],
                  recommendations: list[dict]) -> list[dict]:
    current = _current_map(current_themes)
    previous = _previous_map(previous_themes)
    recs = _recommendation_by_cluster(recommendations)
    changes: list[dict] = []
    used_previous: set[str] = set()

    for cid, row in current.items():
        rec = recs.get(cid)
        prev_id, prev_row = _best_previous(row, previous, used_previous)
        if prev_id:
            used_previous.add(prev_id)
        change_type, detail, priority, before, after = _delta_description(row, prev_row, rec)
        if change_type == "SIN CAMBIO":
            continue
        action = str((rec or {}).get("action") or _action(row)).upper()
        coverage = _coverage(row, rec)
        changes.append({
            "change_id": stable_id(f"{cid}|{change_type}|{detail}", "dlt"),
            "cluster_id": cid,
            "change_type": change_type,
            "priority": priority,
            "action": action,
            "coverage_status": coverage,
            "title": _title(row),
            "url": _url(row),
            "what_changed": detail,
            "before": before,
            "now": after,
            "media_now": _media(row),
            "media_before": _media(prev_row or {}),
            "has_ole": _has_ole(row),
            "ole_match_title": str((rec or {}).get("ole_match_title") or ""),
            "ole_match_url": str((rec or {}).get("ole_match_url") or ""),
            "reason": str((rec or {}).get("reason") or ""),
        })
    changes.sort(key=lambda item: (-item["priority"], item["title"]))
    return changes


def _short_line(item: dict) -> str:
    return f"- {item.get('title','')} — {item.get('what_changed','')}"


def build_summary(changes: list[dict], discoveries: list[dict], recommendations: list[dict],
                  source_health: list[dict], total_topics: int = 0, now: datetime | None = None) -> dict:
    now = now or now_ar()
    actionable = [
        item for item in changes
        if item.get("action") in {"PUBLICAR AHORA", "ACTUALIZAR", "VERIFICAR"}
        and item.get("priority", 0) >= 60
    ]
    publish = [x for x in actionable if x.get("action") == "PUBLICAR AHORA"][:5]
    update = [x for x in actionable if x.get("action") == "ACTUALIZAR"][:5]
    verify = [x for x in actionable if x.get("action") == "VERIFICAR"][:5]
    findings = [x for x in discoveries if x.get("status") in {"HALLAZGO FUERTE", "HALLAZGO"}][:8]
    errors = [x for x in source_health or [] if str(x.get("estado", "")).lower() != "ok"]

    stable_count = max(0, total_topics - len(changes))
    sections: list[str] = [
        f"PANORAMA DEL CORTE\n- {total_topics} temas agrupados; {len(changes)} con cambios reales y {stable_count} sin cambios relevantes."
    ]
    if publish:
        sections.append("PARA EVALUAR AHORA\n" + "\n".join(_short_line(x) for x in publish))
    if update:
        sections.append("QUÉ CAMBIÓ PARA AGREGAR\n" + "\n".join(_short_line(x) for x in update))
    if verify:
        sections.append("QUÉ CONVIENE VERIFICAR\n" + "\n".join(_short_line(x) for x in verify))
    if findings:
        sections.append("HALLAZGOS FIRMES\n" + "\n".join(
            f"- {x.get('title','')} — {x.get('why_it_matters') or x.get('reason','')}" for x in findings
        ))
    if errors:
        sections.append(f"SALUD DE FUENTES\n- {len(errors)} fuente(s) tuvieron problemas en este corte.")

    return {
        "created_at": now.isoformat(timespec="seconds"),
        "title": f"Resumen del corte {now.strftime('%H:%M')}",
        "plain_text": "\n\n".join(sections),
        "publish_count": len(publish),
        "update_count": len(update),
        "verify_count": len(verify),
        "growth_count": 0,
        "discovery_count": len(findings),
        "source_error_count": len(errors),
        "top_change_ids": [x.get("change_id", "") for x in actionable[:10]],
        "top_discovery_ids": [x.get("discovery_id", "") for x in findings[:10]],
    }


def build(current_themes: list[dict], previous_themes: list[dict], recommendations: list[dict],
          discoveries: list[dict], source_health: list[dict]) -> tuple[list[dict], dict]:
    changes = build_changes(current_themes, previous_themes, recommendations)
    summary = build_summary(changes, discoveries, recommendations, source_health, total_topics=len(current_themes or []))
    return changes, summary
