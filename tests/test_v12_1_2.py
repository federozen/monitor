import unittest
from datetime import datetime, timedelta, timezone

from editorial_agents.coverage import best_ole_match, normalize_ole_items
from editorial_agents.date_enrichment import extract_article_dates, enrich_results_dates
from editorial_agents.discovery import generate as generate_discoveries
from editorial_agents.freshness import classify_item
from editorial_agents.utils import TZ_AR, parse_datetime


class V1212DateEnrichmentTests(unittest.TestCase):
    def test_extracts_published_and_modified_jsonld(self):
        html = '''
        <html><head><script type="application/ld+json">
        {"@context":"https://schema.org","@type":"NewsArticle",
         "datePublished":"2026-08-05T20:10:00-03:00",
         "dateModified":"2026-08-05T21:02:00-03:00"}
        </script></head></html>
        '''
        result = extract_article_dates(html)
        self.assertEqual(result["published_at"].hour, 20)
        self.assertEqual(result["updated_at"].hour, 21)
        self.assertEqual(result["published_origin"], "jsonld:datePublished")

    def test_parses_spanish_publisher_dates_but_date_only_is_not_exact(self):
        self.assertEqual(parse_datetime("5 de agosto de 2026, 21:44").hour, 21)
        results = {
            "lanacion": [{
                "titulo": "Una noticia con fecha de listado",
                "url": "https://example.com/deportes/noticia-fechada.html",
                "fecha_publicacion": "5 de agosto de 2026",
                "date_trust": "publisher_timestamp",
                "discovery_channel": "Web directa",
            }]
        }
        stats = enrich_results_dates(results, [{"id": "lanacion", "nombre": "La Nación"}], max_articles=0)
        self.assertEqual(stats["normalized"], 1)
        self.assertEqual(results["lanacion"][0]["date_trust"], "publisher_date_only")

    def test_enriches_direct_article_and_never_promotes_google_news_timestamp(self):
        results = {
            "directa": [{
                "titulo": "River confirmó una baja para el domingo",
                "url": "https://medio.example/deportes/river-baja.html",
                "fecha_publicacion": "",
                "date_trust": "missing",
                "discovery_channel": "Web directa",
            }],
            "gn_river": [{
                "titulo": "River confirmó una baja para el domingo",
                "url": "https://news.google.com/rss/articles/token-nuevo?oc=5",
                "fecha_publicacion": "2026-08-05T23:00:00+00:00",
                "date_trust": "discovery_timestamp",
                "discovery_channel": "Google News",
            }],
        }

        def fake_fetch(url, timeout):
            self.assertEqual(url, "https://medio.example/deportes/river-baja.html")
            return {
                "published_at": datetime(2026, 8, 5, 20, 30, tzinfo=TZ_AR),
                "updated_at": datetime(2026, 8, 5, 21, 15, tzinfo=TZ_AR),
                "published_origin": "jsonld:datePublished",
                "updated_origin": "jsonld:dateModified",
                "final_url": url,
                "status": "ok",
            }

        stats = enrich_results_dates(
            results,
            [{"id": "directa", "nombre": "Medio directo"}, {"id": "gn_river", "nombre": "GNews"}],
            max_articles=10,
            timeout=5,
            workers=1,
            now=datetime(2026, 8, 5, 22, 0, tzinfo=TZ_AR),
            fetcher=fake_fetch,
        )
        direct = results["directa"][0]
        gnews = results["gn_river"][0]
        self.assertEqual(stats["requested"], 1)
        self.assertEqual(direct["date_trust"], "article_metadata")
        self.assertIn("2026-08-05T20:30", direct["fecha_publicacion_verificada"])
        self.assertIn("2026-08-05T21:15", direct["fecha_actualizacion"])
        self.assertEqual(gnews["date_trust"], "discovery_timestamp")

    def test_date_only_cannot_enter_four_hour_summary(self):
        now = datetime(2026, 8, 5, 22, 0, tzinfo=TZ_AR)
        decision = classify_item(
            {"fecha_publicacion": "2026-08-05T12:00:00-03:00", "date_trust": "publisher_date_only"},
            "Noticia sin hora verificable",
            now - timedelta(hours=4),
            now,
        )
        self.assertFalse(decision.accepted)
        self.assertEqual(decision.trust, "publisher_date_only")


class V1212CoverageTests(unittest.TestCase):
    def test_one_shared_club_does_not_create_false_ole_match(self):
        ole = normalize_ole_items([{
            "titulo": "Vinicius: el viaje de su representante a Londres en medio del interés de Arsenal",
            "url": "https://ole.example/vinicius-arsenal",
        }])
        match = best_ole_match("El Betis pulveriza al Arsenal", ole)
        self.assertFalse(match["valid"])
        self.assertLess(match["score"], 0.30)
        self.assertEqual(match["title"], "")
        self.assertEqual(match["url"], "")

    def test_two_teams_and_same_result_event_form_a_valid_match(self):
        ole = normalize_ole_items([{
            "titulo": "El Betis goleó al Arsenal en un amistoso en Dublín",
            "url": "https://ole.example/betis-arsenal",
        }])
        match = best_ole_match("El Betis pulveriza al Arsenal", ole)
        self.assertTrue(match["valid"])
        self.assertIn("arsenal", match["shared_entities"])
        self.assertIn("betis", match["shared_entities"])
        self.assertIn("RESULTADO_GOLEADA", match["shared_events"])


class V1212DiscoveryHierarchyTests(unittest.TestCase):
    def test_global_names_without_core_editorial_signal_stay_candidate(self):
        now = datetime.now(timezone.utc).isoformat()
        discoveries = generate_discoveries({
            "goal": [{
                "titulo": "Cristiano Ronaldo y Messi como ejemplo: ¿abandonó Mohamed Salah el fútbol en su viaje a Trabzon?",
                "url": "https://example.com/salah",
                "publisher_original": "Goal",
                "fecha_publicacion": now,
                "date_trust": "publisher_timestamp",
            }]
        }, [], max_items=5)
        self.assertTrue(discoveries)
        self.assertEqual(discoveries[0]["status"], "CANDIDATO PARA EXPLORAR")

    def test_rare_consequential_story_with_two_sources_is_firm(self):
        now = datetime.now(timezone.utc).isoformat()
        discoveries = generate_discoveries({
            "bbc": [{
                "titulo": "Goalkeeper scores historic 98th-minute goal and wins promotion",
                "url": "https://example.com/keeper-bbc",
                "publisher_original": "BBC Sport",
                "fecha_publicacion": now,
                "date_trust": "publisher_timestamp",
            }],
            "guardian": [{
                "titulo": "Goalkeeper scores historic goal in 98th minute to seal promotion",
                "url": "https://example.com/keeper-guardian",
                "publisher_original": "The Guardian",
                "fecha_publicacion": now,
                "date_trust": "publisher_timestamp",
            }],
        }, [], max_items=5)
        self.assertTrue(discoveries)
        self.assertIn(discoveries[0]["status"], {"HALLAZGO", "HALLAZGO FUERTE"})
        self.assertGreaterEqual(discoveries[0]["confidence"], 68)


if __name__ == "__main__":
    unittest.main()
