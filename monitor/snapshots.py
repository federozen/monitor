from __future__ import annotations


def assess_cut(source_health: list[dict], threshold: float = 0.60) -> dict:
    total = len(source_health)
    healthy = sum(1 for source in source_health if source.get("status") == "ok")
    ratio = healthy / total if total else 0.0
    degraded = total == 0 or ratio < threshold
    return {
        "state": "DEGRADADO" if degraded else "COMPLETO",
        "healthy": healthy,
        "total": total,
        "ratio": ratio,
        "preserve_previous": degraded,
    }


def merge_with_previous(current: list[dict], previous: list[dict], quality: dict) -> list[dict]:
    if not quality.get("preserve_previous"):
        return current
    current_ids = {row.get("story_id") or row.get("cluster_id") for row in current}
    carried = []
    for row in previous:
        story_id = row.get("story_id") or row.get("cluster_id")
        if story_id and story_id not in current_ids:
            copy = dict(row)
            copy["carried_from_previous"] = True
            carried.append(copy)
    return current + carried

