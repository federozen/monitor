"""Demo end-to-end sin red ni credenciales.

Genera reports/DEMO_EDITORIAL.md y reports/demo_output.json con tres historias vivas.
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from editorial_agents.briefing import build as build_briefing
from editorial_agents.desk import build_editorial_desk
from editorial_agents.ole_today import build_ole_today
from editorial_agents.utils import now_ar


def evidence(title: str, url: str, publisher: str, published_at: str, source_id: str) -> dict:
    return {
        "noticia": {
            "titulo": title,
            "url": url,
            "publisher_original": publisher,
            "fecha_publicacion": published_at,
            "date_trust": "publisher_timestamp",
            "discovery_channel": "RSS",
            "source_id": source_id,
        },
        "fuente": {"id": source_id, "nombre": publisher},
    }


def main() -> None:
    now = now_ar().replace(second=0, microsecond=0)
    recent = (now - timedelta(minutes=25)).isoformat()

    previous = [
        {"ClusterID": "c_river_baja", "Titulo": "Un titular de River está en duda", "Medios": "2", "TieneOle": "si", "Accion": "OBSERVAR", "Fuentes": []},
        {"ClusterID": "c_boca_estadio", "Titulo": "Boca evalúa jugar un pendiente en otro estadio", "Medios": "1", "TieneOle": "no", "Accion": "VERIFICAR", "Fuentes": []},
    ]
    themes = [
        {
            "cluster_id": "c_river_baja",
            "titulo": "River confirmó la lesión y la baja por tres semanas de un titular",
            "url": "https://demo.local/river-parte",
            "cant_medios": 3,
            "tiene_ole": True,
            "noticias": [
                evidence("Parte oficial: lesión y baja por tres semanas", "https://demo.local/river-oficial", "River Oficial", recent, "river"),
                evidence("River confirmó el diagnóstico del titular", "https://demo.local/medio-river", "Medio A", recent, "medio_a"),
            ],
        },
        {
            "cluster_id": "c_boca_estadio",
            "titulo": "Boca confirmó que jugará el pendiente en otro estadio",
            "url": "https://demo.local/boca-estadio",
            "cant_medios": 2,
            "tiene_ole": False,
            "noticias": [
                evidence("Comunicado: Boca jugará el pendiente en otro estadio", "https://demo.local/boca-oficial", "Boca Oficial", recent, "boca"),
            ],
        },
    ]
    recommendations = [
        {
            "cluster_id": "c_river_baja", "title": themes[0]["titulo"], "priority": 92,
            "action": "ACTUALIZAR", "coverage_status": "CUBIERTO_CON_DATO_NUEVO",
            "reason": "El parte oficial agrega diagnóstico y plazo a una nota ya publicada.",
            "ole_match_title": "El titular de River que estaba en duda", "ole_match_url": "https://demo.local/ole-river",
        },
        {
            "cluster_id": "c_boca_estadio", "title": themes[1]["titulo"], "priority": 88,
            "action": "PUBLICAR AHORA", "coverage_status": "NO_CUBIERTO",
            "reason": "La posibilidad pasó a comunicado oficial y afecta la logística del partido.",
        },
    ]
    findings = [{
        "discovery_id": "d_keeper",
        "title": "Arquero marcó el gol histórico del ascenso en el minuto 98 y el video se volvió viral",
        "url": "https://demo.local/keeper",
        "status": "HALLAZGO FUERTE",
        "score": 91,
        "noticiability": 91,
        "confidence": 82,
        "confidence_reason": "video oficial; fecha directa; dos publishers originales",
        "signals": ["RAREZA", "VISUAL", "DATO O RECORD", "CONSECUENCIA DEPORTIVA"],
        "suggested_format": "NOTA BREVE + VIDEO",
        "why_it_matters": "Tiene desenlace extraordinario, protagonista claro y material visual.",
        "reason": "rareza; visual; consecuencia deportiva; no hay pieza equivalente en Olé",
        "published_at": recent,
        "date_trust": "publisher_timestamp",
        "publishers": ["Liga Oficial", "Medio Internacional"],
        "evidence": [
            {"publisher": "Liga Oficial", "url": "https://demo.local/keeper-video", "title": "Video oficial del gol del arquero", "published_at": recent},
            {"publisher": "Medio Internacional", "url": "https://demo.local/keeper-cronica", "title": "Goalkeeper scores promotion goal", "published_at": recent},
        ],
    }]
    source_health = [
        {"id": "river", "nombre": "River Oficial", "estado": "ok", "noticias": 4, "canal": "Web directa"},
        {"id": "boca", "nombre": "Boca Oficial", "estado": "ok", "noticias": 3, "canal": "Web directa"},
        {"id": "international", "nombre": "Medio Internacional", "estado": "ok", "noticias": 12, "canal": "RSS"},
    ]

    changes, briefing = build_briefing(themes, previous, recommendations, findings, source_health)
    desk = build_editorial_desk(themes, changes, recommendations, findings, source_health, now=now)
    ole_entries, ole_groups = build_ole_today([
        {"titulo": "El titular de River que estaba en duda", "url": "https://demo.local/ole-river", "fecha_publicacion": (now - timedelta(hours=3)).isoformat(), "fecha_actualizacion": recent, "ole_origin": "ultimas", "ole_page": 1},
        {"titulo": "Boca: hora y TV del próximo partido", "url": "https://demo.local/ole-boca-servicio", "fecha_publicacion": recent, "ole_origin": "ultimas", "ole_page": 1},
    ], [], recommendations, now)

    output = {
        "generated_at": now.isoformat(),
        "changes": changes,
        "briefing": briefing,
        "desk": desk,
        "ole_today": ole_entries,
        "ole_groups": ole_groups,
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "demo_output.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Demo editorial V12", "",
        f"Generada: {now.isoformat(timespec='minutes')}", "",
        "## Resumen del corte", "",
        briefing["plain_text"], "", "## Tres historias vivas", "",
    ]
    for row in desk["topics"]:
        lines += [
            f"### {row['topic']}",
            f"- **Qué cambió:** {row['what_changed']}",
            f"- **Acción:** {row['action']}",
            f"- **Cobertura Olé:** {row['ole_status']}",
            f"- **Por qué importa:** {row['why_it_matters']}", "",
        ]
    lines += ["## Auditoría", "", f"- Ítems auditados: {len(desk['audit'])}", f"- Acciones generadas: {len(desk['actions'])}", f"- Temas Olé agrupados: {len(ole_groups)}", ""]
    (reports / "DEMO_EDITORIAL.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Demo creada: {reports / 'DEMO_EDITORIAL.md'}")


if __name__ == "__main__":
    main()
