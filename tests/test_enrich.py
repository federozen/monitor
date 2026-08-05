"""Pruebas del enriquecimiento de fecha (Fase 2.1), sin red.

Validan la extracción desde JSON-LD, OpenGraph y <time>, y —lo más importante—
que una nota enriquecida termina clasificada como 'confirmada' por el núcleo,
que es lo que la hace entrar al resumen.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from monitor.dates import parse_datetime
from monitor.enrich import extract_published
from monitor.freshness import classify_article, usable_for_summary
from monitor.models import Article
from monitor.sources import RSSFetcher

AHORA = parse_datetime("2026-08-04T12:00:00-03:00")

HTML_JSONLD = """
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"NewsArticle",
 "headline":"River confirmó la baja","datePublished":"2026-08-04T11:20:00-03:00"}
</script>
</head><body>nota</body></html>
"""

HTML_OPENGRAPH = """
<html><head>
<meta property="article:published_time" content="2026-08-04T10:45:00-03:00"/>
</head><body>nota</body></html>
"""

HTML_TIME = """
<html><body><article>
<time datetime="2026-08-04T09:30:00-03:00">hoy</time>
</article></body></html>
"""

HTML_SIN_FECHA = "<html><body><p>sin metadata de fecha</p></body></html>"


class ExtractPublishedTests(unittest.TestCase):
    def test_jsonld(self):
        fecha, origen = extract_published(HTML_JSONLD)
        self.assertEqual(origen, "jsonld")
        self.assertEqual(fecha, parse_datetime("2026-08-04T11:20:00-03:00"))

    def test_opengraph(self):
        fecha, origen = extract_published(HTML_OPENGRAPH)
        self.assertEqual(origen, "opengraph")
        self.assertEqual(fecha, parse_datetime("2026-08-04T10:45:00-03:00"))

    def test_time_tag(self):
        fecha, origen = extract_published(HTML_TIME)
        self.assertEqual(origen, "time_tag")
        self.assertEqual(fecha, parse_datetime("2026-08-04T09:30:00-03:00"))

    def test_sin_fecha_devuelve_none(self):
        self.assertEqual(extract_published(HTML_SIN_FECHA), (None, None))


class EnrichmentPromotesConfidenceTests(unittest.TestCase):
    def test_nota_de_agregador_enriquecida_pasa_a_confirmada(self):
        # Antes: fecha de agregador -> para_verificar -> NO entra al resumen.
        antes = Article(article_id="x", title="River confirmó la baja",
                        url="https://tycsports.com/x", publisher="TyC Sports",
                        date_published=AHORA, date_origin="discovery_timestamp")
        self.assertEqual(classify_article(antes).date_confidence, "para_verificar")
        self.assertFalse(usable_for_summary(antes, AHORA))

        # Enriquecemos con lo que devolvería la página real.
        fecha, origen = extract_published(HTML_JSONLD)
        from dataclasses import replace
        despues = replace(antes, date_published=fecha, date_origin=origen)

        # Ahora sí: confirmada y usable.
        self.assertEqual(classify_article(despues).date_confidence, "confirmada")
        self.assertTrue(usable_for_summary(despues, AHORA))


class FetcherEnrichmentTests(unittest.TestCase):
    def test_fetcher_enriquece_feeds_marcados(self):
        # Fetcher real pero con enrich_url y _fetch_one parcheados: sin red.
        import monitor.sources as src

        def fake_fetch_one(feed, timeout):
            art = Article(article_id="a", title="Boca cierra un refuerzo",
                          url="https://tycsports.com/a", publisher=feed["publisher"],
                          date_published=AHORA, date_origin=feed.get("date_origin", "rss"))
            return [art], {"source_id": feed.get("source_id"), "status": "ok", "count": 1}

        def fake_enrich_url(url, timeout=12):
            return parse_datetime("2026-08-04T11:00:00-03:00"), "jsonld", url

        cfg = {"feeds": [{"source_id": "tyc", "publisher": "TyC",
                          "url": "https://news.google.com/x",
                          "date_origin": "discovery_timestamp", "enrich": True}]}

        orig_fo, orig_eu, orig_load = src._fetch_one, src.enrich_url, RSSFetcher._load
        try:
            src._fetch_one = fake_fetch_one
            src.enrich_url = fake_enrich_url
            RSSFetcher._load = lambda self: cfg
            arts, _ole, salud = RSSFetcher("x").fetch()
        finally:
            src._fetch_one, src.enrich_url, RSSFetcher._load = orig_fo, orig_eu, orig_load

        self.assertEqual(arts[0].date_origin, "jsonld")           # fue enriquecida
        self.assertEqual(salud[0]["enriquecidas"], 1)
        self.assertTrue(usable_for_summary(arts[0], AHORA))       # y ahora es usable


if __name__ == "__main__":
    unittest.main()
