from __future__ import annotations

from .cluster import original_publishers, similarity
from .models import Story


VALID_ACTIONS = {"PUBLICAR", "ACTUALIZAR", "VERIFICAR", "PROFUNDIZAR", "SEGUIR", "DESCARTAR", "NO_HACER_NADA"}


def coverage_status(story: Story, ole_titles: list[str]) -> str:
    if not ole_titles:
        return "NO_CUBIERTO"
    best = max((similarity(story.title, title) for title in ole_titles), default=0.0)
    if best >= 0.45:
        return "YA_CUBIERTO"
    return "COINCIDENCIA_DUDOSA" if best >= 0.20 else "NO_CUBIERTO"


def recommend(story: Story, ole_titles: list[str] | None = None) -> dict:
    publishers = original_publishers(story)
    coverage = coverage_status(story, ole_titles or [])
    official = story.official_confirmed
    if coverage == "YA_CUBIERTO" and not story.changes:
        action, priority = "NO_HACER_NADA", 20
        reason = "Olé ya cubrió el tema y no hay un cambio nuevo registrado."
    elif official and coverage != "YA_CUBIERTO":
        action, priority = "PUBLICAR", 90
        reason = "Hay evidencia oficial y no se encontró una cobertura equivalente de Olé."
    elif len(publishers) >= 2 and coverage == "NO_CUBIERTO":
        action, priority = "VERIFICAR", 75
        reason = "Coinciden medios originales, pero falta una confirmación primaria."
    elif story.changes and coverage == "YA_CUBIERTO":
        action, priority = "ACTUALIZAR", 80
        reason = "Olé ya tiene una pieza, pero la historia incorporó un cambio verificable."
    else:
        action, priority = "SEGUIR", 45
        reason = "La historia merece seguimiento, pero todavía no justifica una acción inmediata."
    return {
        "story_id": story.story_id,
        "title": story.title,
        "action": action,
        "priority": priority,
        "confidence": "alta" if official else "media" if len(publishers) >= 2 else "baja",
        "coverage_status": coverage,
        "reason": reason,
        "publishers": publishers,
        "evidence": [article.url for article in story.articles if article.url],
    }
