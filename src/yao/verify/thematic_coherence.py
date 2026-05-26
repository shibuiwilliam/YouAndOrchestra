"""Thematic coherence analysis — cross-section melodic unity.

Measures how well the main theme (melody) is maintained across sections.
Unlike motif_coherence_score (which measures local 3-gram recurrence),
this module measures:
1. Section-to-section pitch histogram correlation
2. First/last section similarity (A→A′ form)
3. Contour preservation across sections

These metrics detect the specific failure mode where "each section
generates an independent melody with no thematic connection."

Belongs to Layer 5 (Verification).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class ThematicCoherenceReport:
    """Results of thematic coherence analysis.

    Attributes:
        section_correlation: Average pairwise correlation of pitch class
            histograms between consecutive sections. Range [0, 1].
        first_last_similarity: Similarity between first and last section
            pitch distributions. Range [0, 1]. High = A→A′ form achieved.
        contour_preservation: Fraction of section pairs sharing the same
            dominant contour direction. Range [0, 1].
        overall_score: Weighted combination. Range [0, 1].
    """

    section_correlation: float
    first_last_similarity: float
    contour_preservation: float
    overall_score: float


def analyze_thematic_coherence(score: ScoreIR) -> ThematicCoherenceReport:
    """Analyze thematic coherence across sections.

    Args:
        score: The ScoreIR to analyze.

    Returns:
        ThematicCoherenceReport with per-dimension and overall scores.
    """
    if len(score.sections) < 2:
        return ThematicCoherenceReport(
            section_correlation=1.0,
            first_last_similarity=1.0,
            contour_preservation=1.0,
            overall_score=1.0,
        )

    # Extract per-section pitch class histograms and contour directions
    section_histograms: list[dict[int, float]] = []
    section_contours: list[int] = []  # +1=ascending, -1=descending, 0=flat

    for section in score.sections:
        notes: list[Note] = []
        for part in section.parts:
            notes.extend(part.notes)
        notes.sort(key=lambda n: n.start_beat)

        # Pitch class histogram (normalized)
        pc_counts: dict[int, int] = Counter()
        for n in notes:
            pc_counts[n.pitch % 12] += 1
        total = max(sum(pc_counts.values()), 1)
        hist = {k: v / total for k, v in pc_counts.items()}
        section_histograms.append(hist)

        # Dominant contour direction
        if len(notes) >= 2:
            first_half = notes[: len(notes) // 2]
            second_half = notes[len(notes) // 2 :]
            avg_first = sum(n.pitch for n in first_half) / max(len(first_half), 1)
            avg_second = sum(n.pitch for n in second_half) / max(len(second_half), 1)
            if avg_second - avg_first > 2:
                section_contours.append(1)
            elif avg_first - avg_second > 2:
                section_contours.append(-1)
            else:
                section_contours.append(0)
        else:
            section_contours.append(0)

    # 1. Section-to-section pitch histogram correlation
    correlations: list[float] = []
    for i in range(len(section_histograms) - 1):
        corr = _histogram_similarity(section_histograms[i], section_histograms[i + 1])
        correlations.append(corr)
    section_correlation = sum(correlations) / max(len(correlations), 1)

    # 2. First/last section similarity
    first_last_similarity = _histogram_similarity(section_histograms[0], section_histograms[-1])

    # 3. Contour preservation
    if len(section_contours) >= 2:
        matches = sum(1 for i in range(len(section_contours) - 1) if section_contours[i] == section_contours[i + 1])
        contour_preservation = matches / (len(section_contours) - 1)
    else:
        contour_preservation = 1.0

    # Overall: weighted combination
    overall = section_correlation * 0.4 + first_last_similarity * 0.4 + contour_preservation * 0.2

    return ThematicCoherenceReport(
        section_correlation=round(section_correlation, 4),
        first_last_similarity=round(first_last_similarity, 4),
        contour_preservation=round(contour_preservation, 4),
        overall_score=round(overall, 4),
    )


def _histogram_similarity(h1: dict[int, float], h2: dict[int, float]) -> float:
    """Compute cosine similarity between two pitch class histograms.

    Args:
        h1: Normalized histogram (pitch class → weight).
        h2: Normalized histogram.

    Returns:
        Cosine similarity in [0, 1].
    """
    all_keys = set(h1) | set(h2)
    dot = sum(h1.get(k, 0.0) * h2.get(k, 0.0) for k in all_keys)
    mag1 = math.sqrt(sum(v * v for v in h1.values())) or 1e-10
    mag2 = math.sqrt(sum(v * v for v in h2.values())) or 1e-10
    return max(0.0, min(1.0, dot / (mag1 * mag2)))
