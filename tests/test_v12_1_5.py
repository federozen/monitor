from __future__ import annotations

import unittest
from unittest.mock import patch

from editorial_agents.briefing import build_changes


class ChangeQualityTests(unittest.TestCase):
    def test_round_number_seven_is_not_reported_as_new_numeric_fact(self):
        previous = [{
            "cluster_id": "c_programacion",
            "titulo": "Árbitros y TV de la fecha 4 del Torneo Clausura",
            "cant_medios": 3,
            "coverage_status": "YA_CUBIERTO",
            "accion": "OBSERVAR",
            "noticias": [],
        }]
        current = [{
            "cluster_id": "c_programacion",
            "titulo": "Árbitros y TV de la fecha 7 del Torneo Clausura",
            "cant_medios": 4,
            "coverage_status": "YA_CUBIERTO",
            "accion": "OBSERVAR",
            "noticias": [],
        }]
        changes = build_changes(current, previous, [])
        self.assertEqual(changes, [])

    def test_explicit_new_schedule_is_still_a_real_change(self):
        previous = [{
            "cluster_id": "c_partido",
            "titulo": "Boca y Estudiantes jugarán el pendiente",
            "cant_medios": 2,
            "coverage_status": "YA_CUBIERTO",
            "accion": "OBSERVAR",
            "noticias": [],
        }]
        current = [{
            "cluster_id": "c_partido",
            "titulo": "Boca y Estudiantes: nuevo horario confirmado para el pendiente",
            "cant_medios": 3,
            "coverage_status": "YA_CUBIERTO",
            "accion": "OBSERVAR",
            "noticias": [],
        }]
        changes = build_changes(current, previous, [])
        self.assertTrue(changes)
        self.assertIn("fecha, horario o sede", changes[0]["what_changed"])


class ActionSheetTests(unittest.TestCase):
    def test_same_cut_stale_open_actions_are_replaced_by_current_action(self):
        import online_storage as storage

        captured = {}

        def fake_replace(base, headers, rows, min_rows=100):
            material = list(rows)
            captured[base] = material
            return len(material)

        cut = "2026-08-05T20:00_00:00"
        previous = []
        for action_id, new_data in (("act_old_1", "versión inicial"), ("act_old_2", "sumó medios")):
            row = {h: "" for h in storage.ACCIONES_EDITOR_HEADERS}
            row.update({
                "ActionID": action_id,
                "Corte": cut,
                "TemaID": "c_boca",
                "Tema": "Boca venció a Estudiantes",
                "Accion": "ACTUALIZAR",
                "Estado": "PENDIENTE",
                "DatoNuevo": new_data,
                "Actualizado": "2026-08-05T22:00:00-03:00",
            })
            previous.append(row)
        older = {h: "" for h in storage.ACCIONES_EDITOR_HEADERS}
        older.update({
            "ActionID": "act_followup",
            "Corte": "2026-08-05T16:00_20:00",
            "TemaID": "c_otro",
            "Tema": "Seguimiento anterior",
            "Accion": "SEGUIR",
            "Estado": "PENDIENTE",
            "Actualizado": "2026-08-05T19:00:00-03:00",
        })
        previous.append(older)

        desk = {
            "meta": {"cut_key": cut},
            "topics": [],
            "actions": [{
                "action_id": "act_current",
                "cut_key": cut,
                "priority": 100,
                "action": "ACTUALIZAR",
                "status": "PENDIENTE",
                "topic_id": "c_boca",
                "topic": "Boca venció a Estudiantes",
                "new_data": "apareció el parte oficial",
                "updated_at": "2026-08-05T23:00:00-03:00",
            }],
            "audit": [],
            "findings": [],
        }
        with patch.object(storage, "asegurar_estructura"), \
             patch.object(storage, "leer_resumen_4h", return_value=[]), \
             patch.object(storage, "leer_acciones_editor", return_value=previous), \
             patch.object(storage, "_replace", side_effect=fake_replace), \
             patch.object(storage, "_format_editorial_sheet"), \
             patch.object(storage, "_append_rows"):
            storage.guardar_mesa_editorial(desk, [], [], [])

        rows = captured["ACCIONES"]
        self.assertEqual(len(rows), 2)
        current_rows = [row for row in rows if row[1] == cut]
        self.assertEqual(len(current_rows), 1)
        self.assertEqual(current_rows[0][0], "act_current")
        self.assertEqual(current_rows[0][7], "apareció el parte oficial")
        self.assertTrue(any(row[0] == "act_followup" for row in rows))


class OleControlTests(unittest.TestCase):
    def test_control_uses_final_ole_today_publication_range(self):
        import online_storage as storage

        captured = {}

        def fake_replace(base, headers, rows, min_rows=100):
            captured[base] = list(rows)
            return len(captured[base])

        entries = [
            {"published_at": "2026-08-05T06:00:00-03:00", "updated_at": "2026-08-05T07:00:00-03:00"},
            {"published_at": "2026-08-05T20:52:00-03:00", "updated_at": "2026-08-05T22:56:00-03:00"},
        ]
        with patch.object(storage, "leer_control", return_value={"estado": "ok"}), \
             patch.object(storage, "_replace", side_effect=fake_replace):
            storage._actualizar_control_ole_final(entries)

        values = {row[0]: row[1] for row in captured["Control"]}
        self.assertEqual(values["ole_notas_hoy_fechadas"], 2)
        self.assertEqual(values["ole_primera_nota_hoy"], "2026-08-05T06:00-03:00")
        self.assertEqual(values["ole_ultima_nota_hoy"], "2026-08-05T20:52-03:00")
        self.assertEqual(values["ole_ultima_actualizacion_hoy"], "2026-08-05T22:56-03:00")


if __name__ == "__main__":
    unittest.main()
