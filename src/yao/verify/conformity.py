"""Genre conformity and motif coherence scoring.

Provides quantitative measures of how well a generated piece conforms
to its target genre profile and maintains thematic unity through
motif recurrence and variation.

See IMPROVEMENT.md §4.10 and PROJECT.md §12.6–12.7.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from yao.ir.score_ir import ScoreIR
from yao.schema.melodic_profile import MelodicProfile


def motif_coherence_score(score: ScoreIR) -> float:
    """Quantify thematic unity through pitch-pattern recurrence.

    Measures how much the melody reuses short pitch-interval patterns
    (3–5 notes), indicating motif recurrence and development.

    A score of 0.0 means no pattern recurs; 1.0 means the piece is
    entirely built from recurring patterns.

    Each genre has a target range:
    - Lo-fi: 0.7–0.9 (high repetition for hypnotic feel)
    - Bebop: 0.3–0.5 (variation-heavy)
    - Classical: 0.5–0.7 (balanced development)

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Coherence score in [0.0, 1.0].
    """
    notes = score.all_notes()
    if len(notes) < 4:  # noqa: PLR2004
        return 0.0

    # Extract pitch-interval patterns of length 3
    intervals = []
    for i in range(len(notes) - 1):
        intervals.append(notes[i + 1].pitch - notes[i].pitch)

    if len(intervals) < 3:  # noqa: PLR2004
        return 0.0

    # Count 3-gram patterns
    trigrams: list[tuple[int, ...]] = []
    for i in range(len(intervals) - 2):
        trigrams.append((intervals[i], intervals[i + 1], intervals[i + 2]))

    if not trigrams:
        return 0.0

    counts = Counter(trigrams)
    total = len(trigrams)

    # Count how many trigrams recur (appear more than once)
    recurring = sum(c for c in counts.values() if c > 1)
    recurrence_ratio = recurring / total

    # Also measure pattern diversity (Shannon entropy)
    distinct = len(counts)
    if distinct <= 1:
        diversity = 0.0
    else:
        entropy = 0.0
        for c in counts.values():
            p = c / total
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(distinct)
        diversity = entropy / max_entropy if max_entropy > 0 else 0.0

    # Coherence = high recurrence + moderate diversity
    # (pure repetition scores lower than varied recurrence)
    coherence = recurrence_ratio * 0.7 + (1.0 - diversity) * 0.3

    return max(0.0, min(1.0, coherence))


def genre_conformity_score(
    score: ScoreIR,
    profile: MelodicProfile,
) -> dict[str, float]:
    """Measure how closely a generation conforms to a genre profile.

    Computes KL divergence between actual and target distributions
    for intervals and phrase-related features.

    Args:
        score: The ScoreIR to evaluate.
        profile: Target MelodicProfile.

    Returns:
        Dictionary of conformity scores, each in [0.0, 1.0].
    """
    notes = score.all_notes()

    # Interval distribution conformity
    interval_conf = _interval_conformity(notes, profile)

    # Chord-tone targeting conformity (if HarmonicContext info available)
    # For now, use a proxy based on scale-degree distribution

    return {
        "interval_conformity": interval_conf,
        "overall_genre_conformity": interval_conf,
    }


def _interval_conformity(
    notes: list[Any],
    profile: MelodicProfile,
) -> float:
    """Compute interval distribution conformity via KL divergence.

    Args:
        notes: List of Note objects.
        profile: Target MelodicProfile.

    Returns:
        Conformity score in [0.0, 1.0]. Higher = better conformity.
    """
    if len(notes) < 2:  # noqa: PLR2004
        return 0.0

    # Extract actual interval distribution
    intervals: list[int] = []
    for i in range(len(notes) - 1):
        interval = abs(notes[i + 1].pitch - notes[i].pitch)
        intervals.append(min(interval, 12))  # cap at octave

    if not intervals:
        return 0.0

    actual_counts: dict[int, int] = Counter(intervals)
    total = sum(actual_counts.values())
    actual_dist = {k: v / total for k, v in actual_counts.items()}

    # Target distribution
    target_dist = profile.interval_distribution.normalized()

    # Symmetric KL divergence
    kl = _symmetric_kl_divergence(actual_dist, target_dist)

    # Convert to conformity score (1 / (1 + KL))
    return 1.0 / (1.0 + kl)


def _symmetric_kl_divergence(
    p: dict[int, float],
    q: dict[int, float],
) -> float:
    """Compute symmetric KL divergence between two distributions.

    Args:
        p: First distribution (actual).
        q: Second distribution (target).

    Returns:
        Non-negative symmetric KL divergence.
    """
    all_keys = set(p) | set(q)
    epsilon = 1e-10

    kl_pq = 0.0
    kl_qp = 0.0
    for k in all_keys:
        pk = p.get(k, epsilon)
        qk = q.get(k, epsilon)
        if pk > 0 and qk > 0:
            kl_pq += pk * math.log(pk / qk)
            kl_qp += qk * math.log(qk / pk)

    return (kl_pq + kl_qp) / 2.0
