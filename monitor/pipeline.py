"""Orquestador: fuentes → núcleo editorial → planilla.

Es puro respecto de la infraestructura: recibe un `fetcher` (algo con .fetch())
y un `writer` (algo con leer_agenda_previa / escribir_agenda / escribir_snapshot)
inyectados. Por eso se testea entero sin red ni credenciales, con fakes.

Encadena lo que la fase 1 dejó probado:
  1. clasifica la confianza de fecha de cada artículo (freshness);
  2. filtra a lo fresco y certificable dentro de la ventana editorial;
  3. agrupa en historias (cluster);
  4. recomienda una acción por historia, comparando contra Olé;
  5. evalúa la salud del corte y, si está degradado, preserva la Agenda anterior.
"""
from __future__ import annotations

from datetime import datetime

from .cluster import cluster_articles, original_publishers
from .config import EditorialConfig, TZ_AR
from .dates import parse_datetime
from .freshness import usable_for_summary
from .recommendations import recommend
from .snapshots import assess_cut, merge_with_previous


def _fila_agenda(rec: dict, now: datetime) -> dict:
    momento = now.astimezone(TZ_AR)
    return {
        "story_id": rec["story_id"],
        "Fecha": momento.strftime("%Y-%m-%d"),
        "Hora": momento.strftime("%H:%M"),
        "Accion": rec["action"],
        "Prioridad": rec["priority"],
        "Tema": rec["title"],
        "Medios": len(rec["publishers"]),
        "Cobertura_Ole": rec["coverage_status"],
        "Confianza": rec["confidence"],
        "Motivo": rec["reason"],
        "URL": rec["evidence"][0] if rec["evidence"] else "",
        "Estado": "",
    }


def _fila_snapshot(story, run_ts: str) -> list:
    return [
        run_ts,
        story.story_id,
        story.title,
        len(original_publishers(story)),
        "si" if story.official_confirmed else "no",
        story.ole_status,
    ]


def run_pipeline(fetcher, writer, now: datetime | None = None,
                 cfg: EditorialConfig | None = None) -> dict:
    cfg = cfg or EditorialConfig()
    now = parse_datetime(now) or datetime.now(TZ_AR)

    articulos, ole_titles, salud = fetcher.fetch()

    # 1-2. Filtrar a lo publicable en la ventana. usable_for_summary clasifica
    # la confianza de fecha internamente, así que se pasa el artículo crudo:
    # clasificarlo antes lo re-etiquetaría dos veces (classify_article no es
    # idempotente porque reescribe date_origin) y todo caería a "para_verificar".
    frescos = [a for a in articulos if usable_for_summary(a, now, cfg.summary_hours)]

    # 3. Agrupar en historias.
    historias = cluster_articles(frescos)

    # 4. Recomendar por historia (la comparación contra Olé gatea la acción).
    recomendaciones = [recommend(h, ole_titles) for h in historias]
    recomendaciones.sort(key=lambda r: r["priority"], reverse=True)
    tope = cfg.max_summary_topics
    recomendaciones = recomendaciones[:tope]

    # 5. Salud del corte: si está degradado, no pisamos la Agenda buena anterior.
    calidad = assess_cut(salud, cfg.degraded_threshold)
    filas_actuales = [_fila_agenda(r, now) for r in recomendaciones]

    previas = []
    if calidad["preserve_previous"] and writer.disponible():
        previas = writer.leer_agenda_previa()
    filas_finales = merge_with_previous(filas_actuales, previas, calidad)

    escribio = False
    if writer.disponible():
        writer.escribir_agenda(filas_finales)
        run_ts = now.astimezone(TZ_AR).strftime("%Y-%m-%d %H:%M")
        writer.escribir_snapshot([_fila_snapshot(h, run_ts) for h in historias])
        escribio = True

    return {
        "articulos_leidos": len(articulos),
        "articulos_frescos": len(frescos),
        "historias": len(historias),
        "recomendaciones": len(filas_actuales),
        "filas_escritas": len(filas_finales),
        "calidad": calidad["state"],
        "salud": salud,
        "escribio_planilla": escribio,
        "preservo_anterior": calidad["preserve_previous"],
    }
