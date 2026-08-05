"""Google Sheets como tablero de salida del monitor.

Reutiliza EXACTAMENTE el patrón de credenciales del proyecto viejo
(`sheets_memoria.py`): lee GOOGLE_SERVICE_ACCOUNT_JSON + SHEET_ID desde el
entorno (o inyectadas con configure()), y degrada sin romper si faltan.
Por eso los secrets que ya tenés cargados en GitHub/Streamlit funcionan sin
tocar nada.

Pestañas que gestiona (las crea si no existen):
  • Agenda   — el tablero vivo: cada fila es una acción recomendada. El editor
               marca la columna Estado ("hecho" / "descartado").
  • Snapshot — la última corrida (historias detectadas), se reemplaza entera.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

try:
    import gspread
except Exception:  # gspread no instalado: modo degradado
    gspread = None


AGENDA_HEADERS = ["Fecha", "Hora", "Accion", "Prioridad", "Tema", "Medios",
                  "Cobertura_Ole", "Confianza", "Motivo", "URL", "Estado", "Clave"]
SNAPSHOT_HEADERS = ["RunTS", "StoryID", "Titulo", "CantMedios",
                    "OficialConfirmado", "CoberturaOle"]

_conf = {"json": None, "sheet_id": None}
_cache = {"sh": None}


def configure(service_account_json: str | None = None, sheet_id: str | None = None) -> None:
    """Inyecta credenciales desde st.secrets en vez del entorno (igual que el viejo)."""
    if service_account_json:
        _conf["json"] = service_account_json
    if sheet_id:
        _conf["sheet_id"] = sheet_id
    _cache["sh"] = None


def _credenciales() -> tuple[str, str]:
    sa = _conf["json"] or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    sid = _conf["sheet_id"] or os.environ.get("SHEET_ID", "")
    return sa, sid


def disponible() -> bool:
    sa, sid = _credenciales()
    return bool(gspread and sa and sid)


def _sheet():
    if _cache["sh"] is not None:
        return _cache["sh"]
    sa, sid = _credenciales()
    creds = json.loads(sa)
    client = gspread.service_account_from_dict(creds)
    _cache["sh"] = client.open_by_key(sid)
    return _cache["sh"]


def url_planilla() -> str:
    _sa, sid = _credenciales()
    return f"https://docs.google.com/spreadsheets/d/{sid}" if sid else ""


def _ws(nombre: str, headers: list[str]):
    sh = _sheet()
    try:
        ws = sh.worksheet(nombre)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=nombre, rows=400, cols=max(len(headers), 3))
        ws.update(range_name="A1", values=[headers])
    return ws


class SheetWriter:
    """Envoltorio inyectable sobre las pestañas Agenda y Snapshot.

    Los tests pasan un fake con la misma firma (leer_agenda_previa /
    escribir_agenda / escribir_snapshot) y no tocan la red.
    """

    def disponible(self) -> bool:
        return disponible()

    def leer_agenda_previa(self) -> list[dict]:
        """Filas de la Agenda actual como dicts, para preservar en corte degradado."""
        ws = _ws("Agenda", AGENDA_HEADERS)
        filas = ws.get_all_values()
        if not filas or len(filas) < 2:
            return []
        cabecera = filas[0]
        previas = []
        for fila in filas[1:]:
            row = {cabecera[i]: (fila[i] if i < len(fila) else "") for i in range(len(cabecera))}
            row["story_id"] = row.get("Clave", "")
            previas.append(row)
        return previas

    def escribir_agenda(self, filas: list[dict]) -> None:
        ws = _ws("Agenda", AGENDA_HEADERS)
        matriz = [AGENDA_HEADERS]
        for row in filas:
            matriz.append([str(row.get(h, "")) for h in AGENDA_HEADERS])
        ws.clear()
        ws.update(range_name="A1", values=matriz)

    def escribir_snapshot(self, filas: list[list]) -> None:
        ws = _ws("Snapshot", SNAPSHOT_HEADERS)
        matriz = [SNAPSHOT_HEADERS] + [[str(c) for c in fila] for fila in filas]
        ws.clear()
        ws.update(range_name="A1", values=matriz)
