import unittest
from datetime import datetime, timedelta

from editorial_agents.date_enrichment import enrich_cluster_dates
from editorial_agents.desk import build_editorial_desk
from editorial_agents.utils import TZ_AR


class ClusterAwareDateEnrichmentTests(unittest.TestCase):
    def test_spreads_requests_across_unverified_clusters(self):
        now = datetime(2026, 8, 5, 22, 0, tzinfo=TZ_AR)
        first = {
            "titulo": "Historia uno confirmada por dos medios",
            "cant_medios": 2,
            "noticias": [{
                "noticia": {
                    "titulo": "Historia uno confirmada por dos medios",
                    "url": "https://medio-a.example/deportes/historia-uno.html",
                    "date_trust": "missing",
                    "source_id": "medio_a",
                    "discovery_channel": "Web directa",
                },
                "fuente": {"id": "medio_a", "nombre": "Medio A"},
            }],
        }
        second = {
            "titulo": "Historia dos confirmada por dos medios",
            "cant_medios": 2,
            "noticias": [{
                "noticia": {
                    "titulo": "Historia dos confirmada por dos medios",
                    "url": "https://medio-b.example/deportes/historia-dos.html",
                    "date_trust": "missing",
                    "source_id": "medio_b",
                    "discovery_channel": "Web directa",
                },
                "fuente": {"id": "medio_b", "nombre": "Medio B"},
            }],
        }

        def fake_fetch(url, timeout):
            minute = 10 if "uno" in url else 20
            return {
                "published_at": datetime(2026, 8, 5, 21, minute, tzinfo=TZ_AR),
                "updated_at": None,
                "published_origin": "jsonld:datePublished",
                "final_url": url,
                "status": "ok",
            }

        stats = enrich_cluster_dates(
            [first, second], max_clusters=10, max_articles=2, workers=1,
            now=now, fetcher=fake_fetch,
        )
        self.assertEqual(stats["clusters_requested"], 2)
        self.assertEqual(stats["clusters_confirmed"], 2)
        self.assertEqual(first["noticias"][0]["noticia"]["date_trust"], "article_metadata")
        self.assertEqual(second["noticias"][0]["noticia"]["date_trust"], "article_metadata")

    def test_does_not_spend_request_on_cluster_with_trusted_date(self):
        now = datetime(2026, 8, 5, 22, 0, tzinfo=TZ_AR)
        theme = {
            "titulo": "Historia ya fechada",
            "cant_medios": 2,
            "noticias": [{
                "noticia": {
                    "titulo": "Historia ya fechada",
                    "url": "https://medio.example/deportes/ya-fechada.html",
                    "fecha_publicacion": (now - timedelta(minutes=30)).isoformat(),
                    "date_trust": "publisher_timestamp",
                },
                "fuente": {"id": "medio", "nombre": "Medio"},
            }],
        }

        def must_not_run(url, timeout):
            raise AssertionError("No debía consultar una historia ya fechada")

        stats = enrich_cluster_dates([theme], max_articles=10, now=now, fetcher=must_not_run)
        self.assertEqual(stats["requested"], 0)
        self.assertEqual(stats["clusters_confirmed"], 0)


class CandidateFindingVisibilityTests(unittest.TestCase):
    def test_candidate_is_visible_but_not_an_action_or_summary_topic(self):
        now = datetime(2026, 8, 5, 22, 0, tzinfo=TZ_AR)
        candidate = {
            "discovery_id": "d_candidate",
            "title": "Una historia internacional llamativa todavía necesita verificación",
            "url": "https://example.com/candidate",
            "status": "CANDIDATO PARA EXPLORAR",
            "score": 48,
            "noticiability": 48,
            "confidence": 64,
            "published_at": (now - timedelta(minutes=30)).isoformat(),
            "date_trust": "publisher_timestamp",
            "publishers": ["Medio internacional"],
            "signals": ["ALCANCE GLOBAL"],
        }
        desk = build_editorial_desk([], [], [], [candidate], [], now=now)
        self.assertEqual(desk["topics"], [])
        self.assertEqual(desk["actions"], [])
        self.assertEqual(len(desk["findings"]), 1)
        self.assertEqual(desk["findings"][0]["finding_status"], "CANDIDATO PARA EXPLORAR")
        self.assertEqual(desk["findings"][0]["action"], "VERIFICAR")
        self.assertEqual(desk["meta"]["firm_finding_count"], 0)
        self.assertEqual(desk["meta"]["candidate_finding_count"], 1)


if __name__ == "__main__":
    unittest.main()
