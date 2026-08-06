import unittest
from datetime import datetime, timedelta, timezone

from editorial_agents.briefing import build as build_briefing
from editorial_agents.desk import build_editorial_desk
from editorial_agents.discovery import generate as generate_discoveries
from editorial_agents.ole_today import build_ole_today
from editorial_agents.opportunities import generate as generate_opportunities
from editorial_agents.utils import TZ_AR, now_ar


class V12EditorialQualityTests(unittest.TestCase):
    def test_reputable_source_alone_is_not_a_firm_finding(self):
        results = {"bbc": [{
            "titulo": "European club appoints a new assistant coach for next season",
            "url": "https://example.com/routine",
            "publisher_original": "BBC Sport",
            "fecha_publicacion": datetime.now(timezone.utc).isoformat(),
            "date_trust": "publisher_timestamp",
        }]}
        findings = generate_discoveries(results, [], max_items=5)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["status"], "CANDIDATO PARA EXPLORAR")
        self.assertGreater(findings[0]["confidence"], findings[0]["noticiability"])

    def test_candidate_is_audited_but_not_shown_as_firm_finding(self):
        now = now_ar().replace(minute=25, second=0, microsecond=0)
        candidate = {
            "discovery_id": "d_candidate",
            "title": "A club changed a routine stadium access procedure",
            "url": "https://example.com/candidate",
            "status": "CANDIDATO PARA EXPLORAR",
            "score": 38,
            "noticiability": 38,
            "confidence": 82,
            "published_at": (now - timedelta(minutes=20)).isoformat(),
            "date_trust": "publisher_timestamp",
            "publishers": ["BBC Sport"],
        }
        desk = build_editorial_desk([], [], [], [candidate], [], now=now)
        self.assertEqual(desk["topics"], [])
        audit = next(row for row in desk["audit"] if row["item_id"] == "d_candidate")
        self.assertEqual(audit["destination"], "CANDIDATOS")
        self.assertEqual(audit["decision"], "NO_RECOMENDACION_FIRME")

    def test_firm_finding_enters_summary_with_editorial_fields(self):
        now = now_ar().replace(minute=25, second=0, microsecond=0)
        finding = {
            "discovery_id": "d_keeper",
            "title": "Arquero marcó el gol histórico del ascenso en el minuto 98 y el video se volvió viral",
            "url": "https://example.com/keeper",
            "status": "HALLAZGO FUERTE",
            "score": 88,
            "noticiability": 88,
            "confidence": 76,
            "confidence_reason": "fecha directa; dos publishers originales",
            "signals": ["RAREZA", "VISUAL", "DATO O RECORD", "CONSECUENCIA DEPORTIVA"],
            "suggested_format": "NOTA BREVE + VIDEO",
            "why_it_matters": "Tiene un desenlace extraordinario y material visual.",
            "published_at": (now - timedelta(minutes=20)).isoformat(),
            "date_trust": "publisher_timestamp",
            "publishers": ["Medio Uno", "Medio Dos"],
            "evidence": [{"publisher": "Medio Uno", "url": "https://example.com/keeper"}],
        }
        desk = build_editorial_desk([], [], [], [finding], [], now=now)
        self.assertEqual(len(desk["topics"]), 1)
        row = desk["topics"][0]
        self.assertEqual(row["finding_status"], "HALLAZGO FUERTE")
        self.assertEqual(row["suggested_format"], "NOTA BREVE + VIDEO")
        self.assertEqual(row["action"], "PROFUNDIZAR")

    def test_candidate_does_not_generate_derived_opportunity(self):
        candidate = {
            "discovery_id": "d_candidate", "status": "CANDIDATO PARA EXPLORAR",
            "score": 90, "title": "Tema todavía débil", "category": "RADAR INTERNACIONAL",
        }
        self.assertEqual(generate_opportunities([], [candidate]), [])

    def test_more_publishers_alone_is_not_a_real_change(self):
        previous = [{
            "ClusterID": "c_same", "Titulo": "Mismo tema", "Medios": "1",
            "TieneOle": "no", "Accion": "OBSERVAR", "Fuentes": [],
        }]
        current = [{
            "cluster_id": "c_same", "titulo": "Mismo tema", "cant_medios": 4,
            "tiene_ole": False, "accion": "OBSERVAR", "fuentes": [],
        }]
        recs = [{
            "cluster_id": "c_same", "action": "OBSERVAR",
            "coverage_status": "NO_CUBIERTO", "reason": "sin dato nuevo",
        }]
        changes, _ = build_briefing(current, previous, recs, [], [])
        self.assertEqual(changes, [])

    def test_medical_confirmation_is_a_real_change(self):
        previous = [{
            "ClusterID": "c_med", "Titulo": "El jugador está en duda", "Medios": "2",
            "TieneOle": "si", "Accion": "OBSERVAR", "Fuentes": [],
        }]
        current = [{
            "cluster_id": "c_med", "titulo": "Parte oficial confirmó lesión y baja por tres semanas",
            "cant_medios": 2, "tiene_ole": True, "accion": "ACTUALIZAR", "fuentes": [],
        }]
        recs = [{
            "cluster_id": "c_med", "action": "ACTUALIZAR",
            "coverage_status": "CUBIERTO_CON_DATO_NUEVO", "reason": "parte oficial",
        }]
        changes, _ = build_briefing(current, previous, recs, [], [])
        self.assertEqual(len(changes), 1)
        self.assertIn("información médica", changes[0]["what_changed"])

    def test_ole_service_articles_for_boca_and_river_stay_separate(self):
        now = datetime(2026, 8, 5, 18, 0, tzinfo=TZ_AR)
        items = [
            {"titulo": "River vs Central: hora, TV y cómo ver en vivo", "url": "https://ole.test/river", "fecha_publicacion": now.isoformat(), "ole_origin": "ultimas"},
            {"titulo": "Boca vs Newell's: hora, TV y cómo ver en vivo", "url": "https://ole.test/boca", "fecha_publicacion": now.isoformat(), "ole_origin": "ultimas"},
        ]
        entries, groups = build_ole_today(items, [], [], now)
        self.assertEqual(len(entries), 2)
        self.assertEqual(len(groups), 2)

    def test_ole_today_separates_published_and_updated(self):
        now = datetime(2026, 8, 5, 18, 0, tzinfo=TZ_AR)
        items = [
            {"titulo": "Nota publicada hoy con datos confirmados", "url": "https://ole.test/new", "fecha_publicacion": now.isoformat(), "ole_origin": "ultimas"},
            {"titulo": "Nota previa que recibió un dato nuevo oficial", "url": "https://ole.test/upd", "fecha_publicacion": (now - timedelta(days=1)).isoformat(), "fecha_actualizacion": now.isoformat(), "ole_origin": "ultimas"},
        ]
        entries, groups = build_ole_today(items, [], [], now)
        kinds = {row["record_type"] for row in entries}
        self.assertEqual(kinds, {"PUBLICADA_HOY", "ACTUALIZADA_HOY"})
        self.assertEqual(sum(row["published_today"] for row in groups), 1)
        self.assertEqual(sum(row["updated_today"] for row in groups), 1)

    def test_action_id_is_stable_across_cuts_without_real_change(self):
        now1 = datetime(2026, 8, 5, 11, 30, tzinfo=TZ_AR)
        now2 = datetime(2026, 8, 5, 14, 30, tzinfo=TZ_AR)
        def build(now):
            theme = {
                "cluster_id": "c_stable", "titulo": "Club confirmó una baja para el próximo partido",
                "nuevo": True, "cant_medios": 2,
                "noticias": [{"noticia": {"titulo": "Club confirmó una baja", "fecha_publicacion": (now - timedelta(minutes=10)).isoformat(), "date_trust": "publisher_timestamp"}, "fuente": {"nombre": "Club oficial"}}],
            }
            rec = {"cluster_id": "c_stable", "title": theme["titulo"], "action": "ACTUALIZAR", "priority": 80, "coverage_status": "CUBIERTO_CON_DATO_NUEVO"}
            return build_editorial_desk([theme], [], [rec], [], [], now=now)
        id1 = build(now1)["actions"][0]["action_id"]
        id2 = build(now2)["actions"][0]["action_id"]
        self.assertEqual(id1, id2)

    def test_audit_explains_unverified_exclusion(self):
        now = datetime(2026, 8, 5, 18, 0, tzinfo=TZ_AR)
        theme = {
            "cluster_id": "c_gnews", "titulo": "Historia reindexada sin fecha directa", "cant_medios": 2,
            "noticias": [{"noticia": {"titulo": "Historia reindexada sin fecha directa", "fecha_publicacion": now.isoformat(), "date_trust": "discovery_timestamp"}, "fuente": {"id": "gn_test", "nombre": "Google News"}}],
        }
        desk = build_editorial_desk([theme], [], [], [], [], now=now)
        self.assertEqual(desk["topics"], [])
        self.assertEqual(desk["audit"][0]["destination"], "EXCLUIDO")
        self.assertIn("NO VERIFICADA", desk["audit"][0]["reason"])


if __name__ == "__main__":
    unittest.main()

class V12StorageContractTests(unittest.TestCase):
    def test_editorial_rows_match_headers_and_terminal_action_is_not_repeated(self):
        from unittest.mock import patch
        import online_storage as storage

        captured = {}
        def fake_replace(base, headers, rows, min_rows=100):
            material = list(rows)
            captured[base] = (headers, material)
            for row in material:
                self.assertEqual(len(row), len(headers), base)
            return len(material)

        desk = {
            "meta": {"cut_key": "2026-08-05T16:00_20:00"},
            "topics": [{
                "cut_key": "2026-08-05T16:00_20:00", "topic": "Hallazgo de prueba",
                "section": "HALLAZGOS", "finding_status": "HALLAZGO", "priority": 70,
                "noticiability": 72, "confidence": 80, "signals": ["RAREZA", "VISUAL"],
                "confidence_reason": "fecha directa", "what_happened": "Ocurrió un hecho raro",
                "why_it_matters": "Tiene valor editorial", "ole_status": "NO_CUBIERTO",
                "action": "SEGUIR", "suggested_format": "NOTA BREVE", "sources": "Fuente",
                "source_urls": "https://example.com/fuente", "url": "https://example.com/tema",
            }],
            "actions": [{
                "action_id": "act_same", "cut_key": "2026-08-05T16:00_20:00", "priority": 70,
                "action": "SEGUIR", "status": "PENDIENTE", "topic_id": "d_1", "topic": "Hallazgo",
                "new_data": "Sin cambio", "updated_at": "2026-08-05T18:00:00-03:00",
            }],
            "audit": [{
                "cut_key": "2026-08-05T16:00_20:00", "item_type": "HALLAZGO", "item_id": "d_1",
                "freshness_state": "CONFIRMADA_O_PROBABLE", "destination": "RESUMEN_4H",
                "topic": "Hallazgo", "reference_date": "2026-08-05T17:30:00-03:00",
                "date_type": "publisher_timestamp", "decision": "SEGUIR", "reason": "Rareza",
                "sources": "Fuente", "url": "https://example.com/tema",
            }],
        }
        old_actions = [{h: "" for h in storage.ACCIONES_EDITOR_HEADERS}]
        old_actions[0].update({"ActionID": "act_same", "Estado": "HECHO"})
        with patch.object(storage, "asegurar_estructura"), \
             patch.object(storage, "leer_resumen_4h", return_value=[]), \
             patch.object(storage, "leer_acciones_editor", return_value=old_actions), \
             patch.object(storage, "_replace", side_effect=fake_replace), \
             patch.object(storage, "_format_editorial_sheet"), \
             patch.object(storage, "_append_rows"):
            counts = storage.guardar_mesa_editorial(desk, [], [], [])
        self.assertEqual(len(captured["ACCIONES"][1]), 1)
        self.assertEqual(captured["ACCIONES"][1][0][4], "HECHO")
        self.assertEqual(counts["audit"], 1)

class V121NewSheetDefaultsTests(unittest.TestCase):
    def test_sheet_names_have_no_prefix_by_default(self):
        from unittest.mock import patch
        import online_storage as storage

        old = storage._CONF["prefix"]
        try:
            storage._CONF["prefix"] = None
            with patch.dict("os.environ", {}, clear=True):
                self.assertEqual(storage.nombre_pestana("RESUMEN_4H"), "RESUMEN_4H")
                self.assertEqual(storage.nombre_pestana("ACCIONES"), "ACCIONES")
        finally:
            storage._CONF["prefix"] = old

    def test_native_configuration_does_not_depend_on_legacy_sheet(self):
        from unittest.mock import patch
        import online_storage as storage

        rows = [
            {"Clave": "zona_horaria", "Valor": "America/Argentina/Buenos_Aires", "Descripcion": ""},
            {"Clave": "max_temas_resumen", "Valor": "40", "Descripcion": ""},
        ]
        with patch.object(storage, "_records", return_value=rows) as mocked:
            config = storage.leer_configuracion()
        mocked.assert_called_once_with("CONFIGURACION", storage.CONFIGURACION_HEADERS)
        self.assertEqual(config["max_temas_resumen"], "40")

class V1211RegressionTests(unittest.TestCase):
    def test_cluster_id_is_shared_by_storage_curator_briefing_and_desk(self):
        import online_storage as storage
        from editorial_agents.curator import curate
        from editorial_agents.briefing import build_changes
        from editorial_agents.utils import canonical_cluster_id

        now = datetime(2026, 8, 5, 21, 30, tzinfo=TZ_AR)
        title = "El Betis pulveriza al Arsenal"
        expected = storage.cluster_id(title)
        self.assertEqual(canonical_cluster_id(title), expected)

        theme = {
            "titulo": title,
            "url": "https://example.com/betis",
            "cant_medios": 2,
            "tiene_ole": False,
            "noticias": [{
                "noticia": {
                    "titulo": title,
                    "url": "https://example.com/betis",
                    "fecha_publicacion": (now - timedelta(minutes=20)).isoformat(),
                    "date_trust": "publisher_timestamp",
                    "publisher_original": "Fuente Uno",
                },
                "fuente": {"id": "source_one", "nombre": "Fuente Uno"},
            }],
        }
        recs = curate([theme], [{"titulo": title, "nuevo": True, "delta": 1}], {})
        self.assertEqual(recs[0]["cluster_id"], expected)

        changes = build_changes([theme], [], recs)
        self.assertEqual(changes[0]["cluster_id"], expected)

        desk = build_editorial_desk([theme], changes, recs, [], [], now=now)
        self.assertEqual(desk["topics"][0]["topic_id"], expected)
        self.assertEqual(len(desk["actions"]), 1)
        self.assertEqual(desk["actions"][0]["action"], "PUBLICAR AHORA")

    def test_firm_recent_discovery_stays_in_visible_findings_outside_fixed_block(self):
        now = datetime(2026, 8, 5, 21, 40, tzinfo=TZ_AR)
        finding = {
            "discovery_id": "d_recent",
            "title": "Arquero marcó el gol del ascenso en el minuto 98",
            "url": "https://example.com/keeper",
            "status": "HALLAZGO",
            "score": 75,
            "noticiability": 75,
            "confidence": 72,
            "signals": ["RAREZA", "VISUAL"],
            "why_it_matters": "Tiene desenlace extraordinario y video oficial.",
            # 18:30 AR: dentro de las últimas cuatro horas, pero antes del bloque fijo 20:00.
            "published_at": datetime(2026, 8, 5, 18, 30, tzinfo=TZ_AR).isoformat(),
            "date_trust": "publisher_timestamp",
            "publishers": ["Fuente oficial"],
            "evidence": [{"publisher": "Fuente oficial", "url": "https://example.com/keeper"}],
        }
        desk = build_editorial_desk([], [], [], [finding], [], now=now)
        self.assertEqual(desk["topics"], [])
        self.assertEqual(len(desk["findings"]), 1)
        self.assertEqual(desk["findings"][0]["topic"], finding["title"])
