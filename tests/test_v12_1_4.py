from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from editorial_agents.briefing import build_changes
from editorial_agents.coverage import enrich_theme_coverage
from editorial_agents.curator import curate
from editorial_agents.desk import build_editorial_desk
from editorial_agents.story_merge import consolidate_stories

AR = ZoneInfo("America/Argentina/Buenos_Aires")


def evidence(title: str, publisher: str, source_id: str, url: str, published: str, channel: str = "Web directa") -> dict:
    return {
        "noticia": {
            "titulo": title,
            "publisher_original": publisher,
            "source_id": source_id,
            "url": url,
            "url_final": url,
            "fecha_publicacion": published,
            "date_trust": "article_metadata",
            "discovery_channel": channel,
        },
        "fuente": {"id": source_id, "nombre": publisher, "url": url},
    }


class StoryMergeTests(unittest.TestCase):
    def test_match_result_angles_become_one_live_story(self):
        clusters = [
            {
                "titulo": "Boca derrotó 1-0 a Estudiantes y logró su primera victoria en el Clausura",
                "cant_medios": 4,
                "medios_originales": ["Olé", "TN", "Clarín", "Infobae"],
                "fuente_ids": ["ole", "tn", "clarin", "infobae"],
                "noticias": [
                    evidence("Boca derrotó 1-0 a Estudiantes y logró su primera victoria en el Clausura", "Olé", "ole", "https://ole.test/boca-estudiantes", "2026-08-05T21:00:00-03:00"),
                ],
                "nac": 4, "intl": 0,
            },
            {
                "titulo": "Cortó la racha: Boca venció a Estudiantes con gol de Ascacibar",
                "cant_medios": 3,
                "medios_originales": ["La Nación", "El Gráfico", "Infocielo"],
                "fuente_ids": ["lanacion", "elgrafico", "cielosports"],
                "noticias": [
                    evidence("Cortó la racha: Boca venció a Estudiantes con gol de Ascacibar", "La Nación", "lanacion", "https://lanacion.test/boca-estudiantes", "2026-08-05T21:20:00-03:00"),
                ],
                "nac": 3, "intl": 0,
            },
            {
                "titulo": "Con Boca en zona de Sudamericana: así quedó la tabla anual",
                "cant_medios": 2,
                "medios_originales": ["Olé", "TyC"],
                "fuente_ids": ["ole", "tyc"],
                "noticias": [
                    evidence("Con Boca en zona de Sudamericana: así quedó la tabla anual", "Olé", "ole", "https://ole.test/tabla", "2026-08-05T21:30:00-03:00"),
                ],
                "nac": 2, "intl": 0,
            },
        ]
        merged = consolidate_stories(clusters)
        self.assertEqual(len(merged), 2)
        match_story = max(merged, key=lambda row: row.get("cant_medios", 0))
        self.assertEqual(match_story["cant_medios"], 7)
        self.assertEqual(match_story.get("_merged_cluster_count"), 2)
        self.assertTrue(any("tabla anual" in row["titulo"].lower() for row in merged))


class CoverageAndPriorityTests(unittest.TestCase):
    def test_direct_ole_article_wins_over_unrelated_approximate_match(self):
        theme = {
            "titulo": "Show de Messi en Inter Miami: doblete y asistencia ante San Luis",
            "noticias": [
                evidence("Video: doblete de Messi y asistencia ante Atlético San Luis", "Olé", "ole", "https://ole.test/messi-san-luis", "2026-08-05T22:30:00-03:00"),
                evidence("Show de Messi en Inter Miami: doblete y asistencia ante San Luis", "La Nación", "lanacion", "https://lanacion.test/messi", "2026-08-05T22:35:00-03:00"),
            ],
        }
        ole_items = [{"title": "Enner Valencia llega a Boca tras el Mundial", "url": "https://ole.test/enner"}]
        enriched = enrich_theme_coverage(theme, ole_items)
        self.assertNotEqual(enriched["coverage_status"], "NO_CUBIERTO")
        self.assertEqual(enriched["ole_match_url"], "https://ole.test/messi-san-luis")

    def test_routine_foreign_story_is_not_publish_now(self):
        theme = {
            "titulo": "Remontada de Jódar para empezar en Montreal",
            "cant_medios": 3,
            "medios_originales": ["Marca", "Mundo Deportivo", "Sport"],
            "nac": 0,
            "intl": 3,
            "coverage_status": "NO_CUBIERTO",
            "noticias": [
                evidence("Remontada de Jódar para empezar en Montreal", "Marca", "marca", "https://marca.test/jodar", "2026-08-05T20:27:00-03:00"),
                evidence("Remontada espectacular de Rafa Jódar en Montréal", "Mundo Deportivo", "mundodep", "https://md.test/jodar", "2026-08-05T20:30:00-03:00"),
            ],
        }
        rec = curate([theme], [], {"max_age_hours": 8})[0]
        self.assertEqual(rec["action"], "OBSERVAR")
        self.assertIn("sin conexion argentina", rec["reason"])

    def test_generic_live_result_does_not_match_unrelated_ole_game(self):
        theme = {
            "titulo": "Peñarol vs. Wanderers (5 de Ago., 2026) Resultados en Vivo",
            "noticias": [],
        }
        ole_items = [{
            "title": "Boca vs. Estudiantes, resultados en vivo por la Liga Profesional 2026",
            "url": "https://ole.test/boca-estudiantes",
        }]
        enriched = enrich_theme_coverage(theme, ole_items)
        self.assertEqual(enriched["coverage_status"], "NO_CUBIERTO")
        self.assertEqual(enriched["ole_match_url"], "")

    def test_argentine_upset_remains_actionable(self):
        theme = {
            "titulo": "Thiago Tirante eliminó a Taylor Fritz en Montreal",
            "cant_medios": 3,
            "medios_originales": ["Infobae", "Clarín", "La Voz"],
            "nac": 3,
            "intl": 0,
            "coverage_status": "NO_CUBIERTO",
            "noticias": [
                evidence("Thiago Tirante eliminó a Taylor Fritz en Montreal", "Infobae", "infobae", "https://infobae.test/tirante", "2026-08-05T22:39:00-03:00"),
            ],
        }
        rec = curate([theme], [], {"max_age_hours": 8})[0]
        self.assertEqual(rec["action"], "PUBLICAR AHORA")


class EditorialOutputTests(unittest.TestCase):
    def test_score_digits_do_not_become_fake_new_data(self):
        previous = [{
            "titulo": "Boca vs Estudiantes: hora y TV",
            "cant_medios": 3,
            "coverage_status": "YA_CUBIERTO",
            "noticias": [],
        }]
        current = [{
            "titulo": "Boca derrotó 1-0 a Estudiantes",
            "cant_medios": 4,
            "coverage_status": "CUBIERTO_CON_DATO_NUEVO",
            "noticias": [],
        }]
        recs = [{
            "cluster_id": "c_ignored",
            "title": current[0]["titulo"],
            "action": "ACTUALIZAR",
            "coverage_status": "CUBIERTO_CON_DATO_NUEVO",
        }]
        # Use the real canonical id generated by build_changes lookup path.
        from editorial_agents.utils import canonical_cluster_id
        recs[0]["cluster_id"] = canonical_cluster_id(current[0]["titulo"])
        changes = build_changes(current, previous, recs)
        self.assertTrue(changes)
        self.assertNotIn("dato numérico 0", changes[0]["what_changed"])
        self.assertNotIn("dato numérico 1", changes[0]["what_changed"])

    def test_low_priority_information_is_not_labeled_indispensable(self):
        now = datetime(2026, 8, 5, 22, 40, tzinfo=AR)
        theme = {
            "titulo": "Tema cubierto sin novedad",
            "cant_medios": 2,
            "coverage_status": "YA_CUBIERTO",
            "noticias": [
                evidence("Tema cubierto sin novedad", "Olé", "ole", "https://ole.test/tema", "2026-08-05T22:00:00-03:00"),
            ],
        }
        desk = build_editorial_desk([theme], [], [{
            "cluster_id": __import__('editorial_agents.utils', fromlist=['canonical_cluster_id']).canonical_cluster_id(theme["titulo"]),
            "title": theme["titulo"],
            "action": "OBSERVAR",
            "priority": 40,
            "coverage_status": "YA_CUBIERTO",
        }], [], [], now=now, min_topics=1, max_topics=5)
        self.assertEqual(desk["topics"][0]["importance"], "PANORAMA")


if __name__ == "__main__":
    unittest.main()
