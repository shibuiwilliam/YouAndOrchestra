"""Memorability proxy — estimate melodic memorability from acoustic features.

Combines pitch-sequence autocorrelation, contour predictability, and
average cadence strength into a single memorability score.

See PROJECT.md §12.8 and IMPROVEMENT.md §4.10.
"""

from __future__ import annotations

from yao.ir.score_ir import ScoreIR


def memorability_proxy(score: ScoreIR) -> float:
    """Estimate melodic memorability.

    Combines three components:
    1. Repetition strength: autocorrelation of the pitch sequence
    2. Contour predictability: how predictable the melodic direction is
    3. Simplicity: preference for stepwise motion and moderate range

    A perfectly memorable melody scores ~0.7–0.9 (some repetition,
    predictable but not boring). Pure randomness scores ~0.2.
    Pure repetition scores ~0.6 (catchy but monotonous).

    Args:
        score: The ScoreIR to analyze.

    Returns:
        Memorability score in [0.0, 1.0].
    """
    notes = score.all_notes()
    if len(notes) < 4:  # noqa: PLR2004
        return 0.0

    pitches = [n.pitch for n in notes]

    rep_strength = _repetition_strength(pitches)
    contour_pred = _contour_predictability(pitches)
    simplicity = _simplicity_score(pitches)

    # Weighted combination
    return rep_strength * 0.4 + contour_pred * 0.3 + simplicity * 0.3


def _repetition_strength(pitches: list[int]) -> float:
    """Measure pitch-sequence repetition via autocorrelation.

    Checks how often short patterns (2–4 notes) recur.

    Args:
        pitches: List of MIDI pitches.

    Returns:
        Repetition score in [0.0, 1.0].
    """
    if len(pitches) < 4:  # noqa: PLR2004
        return 0.0

    # Convert to intervals
    intervals = [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]

    # Count recurring 2-grams and 3-grams
    bigrams = [tuple(intervals[i : i + 2]) for i in range(len(intervals) - 1)]
    trigrams = [tuple(intervals[i : i + 3]) for i in range(len(intervals) - 2)]

    if not bigrams:
        return 0.0

    unique_bi_ratio = len(set(bigrams)) / len(bigrams)
    unique_tri_ratio = len(set(trigrams)) / len(trigrams) if trigrams else 1.0

    # Lower unique ratio → more repetition → higher score
    bi_score = 1.0 - unique_bi_ratio
    tri_score = 1.0 - unique_tri_ratio

    return bi_score * 0.5 + tri_score * 0.5


def _contour_predictability(pitches: list[int]) -> float:
    """Measure how predictable the melodic direction is.

    Counts the proportion of direction changes vs. continuations.
    Moderate predictability (0.5–0.7) is best for memorability.

    Args:
        pitches: List of MIDI pitches.

    Returns:
        Predictability score in [0.0, 1.0].
    """
    if len(pitches) < 3:  # noqa: PLR2004
        return 0.5

    directions = []
    for i in range(len(pitches) - 1):
        diff = pitches[i + 1] - pitches[i]
        if diff > 0:
            directions.append(1)
        elif diff < 0:
            directions.append(-1)
        else:
            directions.append(0)

    # Count continuations (same direction as previous)
    continuations = 0
    for i in range(1, len(directions)):
        if directions[i] == directions[i - 1]:
            continuations += 1

    total = len(directions) - 1
    if total <= 0:
        return 0.5

    continuation_ratio = continuations / total

    # Best memorability at ~0.5–0.7 continuation ratio
    # Map using a bell curve centered at 0.6
    deviation = abs(continuation_ratio - 0.6)
    return max(0.0, 1.0 - deviation * 2.5)


def _simplicity_score(pitches: list[int]) -> float:
    """Score melodic simplicity (stepwise motion, moderate range).

    Memorable melodies tend to use mostly small intervals and a
    comfortable range.

    Args:
        pitches: List of MIDI pitches.

    Returns:
        Simplicity score in [0.0, 1.0].
    """
    if len(pitches) < 2:  # noqa: PLR2004
        return 0.5

    # Proportion of stepwise motion (intervals of 1–2 semitones)
    stepwise = 0
    for i in range(len(pitches) - 1):
        if abs(pitches[i + 1] - pitches[i]) <= 2:  # noqa: PLR2004
            stepwise += 1

    step_ratio = stepwise / (len(pitches) - 1)

    # Range score: penalize extremes
    pitch_range = max(pitches) - min(pitches)
    if pitch_range <= 12:  # within an octave
        range_score = 1.0
    elif pitch_range <= 19:  # within 1.5 octaves
        range_score = 0.7
    elif pitch_range <= 24:  # within 2 octaves
        range_score = 0.4
    else:
        range_score = 0.2

    return step_ratio * 0.6 + range_score * 0.4
