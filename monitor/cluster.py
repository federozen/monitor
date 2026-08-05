from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from .models import Article, Story


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def tokens(value: str) -> set[str]:
    return {word for word in normalize_text(value).split() if len(word) >= 4}


def similarity(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def stable_story_id(article: Article) -> str:
    import hashlib
    key = normalize_text(article.title)[:180]
    return "story_" + hashlib.sha1(key.encode()).hexdigest()[:12]


def cluster_articles(articles: list[Article], threshold: float = 0.22) -> list[Story]:
    stories: list[Story] = []
    for article in articles:
        target = next((story for story in stories if similarity(story.title, article.title) >= threshold), None)
        if target is None:
            target = Story(story_id=stable_story_id(article), title=article.title)
            stories.append(target)
        target.articles.append(article)
        dates = [x.date_published or x.date_updated for x in target.articles if x.date_published or x.date_updated]
        if dates:
            target.first_seen = min(dates)
            target.last_change = max(dates)
        target.official_confirmed = target.official_confirmed or article.publisher.lower().endswith("oficial")
    return stories


def original_publishers(story: Story) -> list[str]:
    return sorted({article.publisher for article in story.articles if article.publisher})
