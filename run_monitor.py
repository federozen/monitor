"""Punto de entrada de la Fase 2: fuentes reales → núcleo → Google Sheets.

Uso local:
    python run_monitor.py

Requiere en el entorno (los mismos secrets del proyecto viejo):
    GOOGLE_SERVICE_ACCOUNT_JSON   el JSON completo de la service account
    SHEET_ID                      el ID de la planilla

Si faltan credenciales, corre igual en modo simulacro: procesa las fuentes y
te muestra en pantalla qué habría escrito, sin tocar la planilla. Útil para
probar sin riesgo.
"""
from __future__ import annotations

import sys
from pathlib import Path

from monitor.config import EditorialConfig
from monitor.pipeline import run_pipeline
from monitor.sheets import SheetWriter, disponible, url_planilla
from monitor.sources import RSSFetcher

SOURCES = Path(__file__).parent / "sources.json"

# Protección: si respondieron muy pocas fuentes, preferimos no escribir nada
# antes que ensuciar la memoria con una corrida mala (misma idea que el vigía).
MIN_FUENTES_OK = 2


def main() -> int:
    fetcher = RSSFetcher(SOURCES)
    writer = SheetWriter()
    cfg = EditorialConfig()

    print("→ Leyendo fuentes…")
    resumen = run_pipeline(fetcher, writer, cfg=cfg)

    ok = sum(1 for s in resumen["salud"] if s.get("status") == "ok")
    total = len(resumen["salud"])
    print(f"   fuentes que respondieron: {ok}/{total}")
    for s in resumen["salud"]:
        marca = {"ok": "✓", "vacio": "∅", "error": "✗"}.get(s.get("status"), "?")
        if s.get("reason"):
            detalle = f" ({s['reason']})"
        else:
            detalle = f" · {s.get('count', 0)} notas"
            if "enriquecidas" in s:
                detalle += f" · {s['enriquecidas']} con fecha real"
        print(f"     {marca} {s['source_id']}{detalle}")

    print(f"   artículos leídos: {resumen['articulos_leidos']} · "
          f"frescos y certificables: {resumen['articulos_frescos']}")
    print(f"   historias: {resumen['historias']} · recomendaciones: {resumen['recomendaciones']}")
    print(f"   estado del corte: {resumen['calidad']}"
          + ("  (se preservó la Agenda anterior)" if resumen["preservo_anterior"] else ""))

    if ok < MIN_FUENTES_OK:
        print("⚠  Muy pocas fuentes respondieron: no se escribe la planilla (protección).")
        return 0

    if resumen["escribio_planilla"]:
        print(f"✓ Planilla actualizada: {url_planilla()}")
    elif disponible():
        print("⚠  Había credenciales pero no se escribió (revisá el log de arriba).")
    else:
        print("ℹ  Sin credenciales: modo simulacro. Cargá GOOGLE_SERVICE_ACCOUNT_JSON "
              "y SHEET_ID para escribir en tu planilla.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
