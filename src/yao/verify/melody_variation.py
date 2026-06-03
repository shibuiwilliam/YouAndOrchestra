"""Melody variation metrics.

Quantifies whether a motif recurs across sections in recognizable form.
Good compositions have section_similarity in 0.35-0.85 (not too same, not too different).

Belongs to Layer 5 (Verify).
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.plan.motif import MotifPlan
from yao.ir.score_ir import ScoreIR


def melody_section_similarity(score: ScoreIR) -> dict[str, float]:
    """Compute pairwise melodic contour similarity between sections.

    Args:
        score: The generated score.

    Returns:
        Dict of "sectionA-sectionB" → similarity (0=different, 1=identical).
    """
    sections = score.sections
    if len(sections) < 2:  # noqa: PLR2004
        return {}

    contours: dict[str, list[int]] = {}
    for section in sections:
        melody_notes: list[Note] = []
        for part in section.parts:
            if part.instrument != "drum_kit":
                melody_notes.extend(part.notes)
        melody_notes.sort(key=lambda n: n.start_beat)
        if len(melody_notes) >= 2:  # noqa: PLR2004
            intervals = [
                melody_notes[i].pitch - melody_notes[i - 1].pitch for i in range(1, min(20, len(melody_notes)))
            ]
            contours[section.name] = intervals

    similarities: dict[str, float] = {}
    names = list(contours.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sim = _contour_similarity(contours[a], contours[b])
            similarities[f"{a}-{b}"] = sim

    return similarities


def _contour_similarity(a: list[int], b: list[int]) -> float:
    """Compute contour direction similarity between two interval sequences."""
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    matches = sum(1 for i in range(n) if (a[i] > 0) == (b[i] > 0))
    return matches / n


def motif_recurrence_score(plan: MotifPlan | None) -> float:
    """Fraction of sections that contain the primary motif (M1).

    Good variation should be >= 0.7 (motif appears in most sections).

    Args:
        plan: The motif plan. None returns 0.0.

    Returns:
        Score from 0.0 to 1.0.
    """
    if plan is None or not plan.placements:
        return 0.0
    sections_with_m1: set[str] = set()
    all_sections: set[str] = set()
    for p in plan.placements:
        all_sections.add(p.section_id)
        if p.motif_id == "M1":
            sections_with_m1.add(p.section_id)
    return len(sections_with_m1) / len(all_sections) if all_sections else 0.0
