import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from monitor.cluster import cluster_articles, original_publishers
from monitor.dates import parse_datetime
from monitor.freshness import classify_article, usable_for_summary
from monitor.models import Article
from monitor.recommendations import recommend
from monitor.snapshots import assess_cut, merge_with_previous


class CoreEditorialTests(unittest.TestCase):
    def setUp(self):
        fixture = json.loads((Path(__file__).parents[1] / "fixtures" / "corte_basico.json").read_text(encoding="utf-8"))
        self.now = parse_datetime(fixture["now"])
        self.articles = [Article(**{**row, "date_published": parse_datetime(row["date_published"])}) for row in fixture["articles"]]
        self.ole_titles = fixture["ole_titles"]

    def test_google_news_timestamp_does_not_enter_summary(self):
        old = self.articles[-1]
        self.assertEqual(classify_article(old).date_confidence, "para_verificar")
        self.assertFalse(usable_for_summary(old, self.now))

    def test_direct_and_rss_dates_are_usable(self):
        self.assertEqual(classify_article(self.articles[0]).date_confidence, "confirmada")
        self.assertEqual(classify_article(self.articles[1]).date_confidence, "probable")
        self.assertTrue(usable_for_summary(self.articles[0], self.now))

    def test_cluster_keeps_articles_and_publishers(self):
        stories = cluster_articles(self.articles[:2])
        self.assertEqual(len(stories), 1)
        self.assertEqual(original_publishers(stories[0]), ["River Oficial", "TyC Sports"])

    def test_recommendation_explains_update_when_ole_has_old_angle(self):
        story = cluster_articles(self.articles[:2])[0]
        story.changes.append({"before": "sin parte", "after": "baja confirmada"})
        rec = recommend(story, self.ole_titles)
        self.assertEqual(rec["action"], "ACTUALIZAR")
        self.assertTrue(rec["evidence"])

    def test_degraded_cut_preserves_previous_snapshot(self):
        quality = assess_cut([{ "status": "error" }, { "status": "ok" }])
        self.assertEqual(quality["state"], "DEGRADADO")
        merged = merge_with_previous([{ "story_id": "new" }], [{ "story_id": "old" }], quality)
        self.assertEqual(len(merged), 2)
        self.assertTrue(merged[-1]["carried_from_previous"])


if __name__ == "__main__":
    unittest.main()

