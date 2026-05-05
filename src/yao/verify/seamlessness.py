"""Seamless loop evaluator — checks boundary continuity for loopable pieces.

Evaluates whether a ScoreIR can loop seamlessly by checking:
- No notes cut off at boundaries
- Energy (velocity) continuity across the loop point
- Pitch continuity (no jarring leaps at the seam)

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR


def evaluate_seamlessness(score: ScoreIR) -> float:
    """Evaluate how seamlessly a ScoreIR can loop.

    Checks three dimensions:
    1. No notes are cut off at the loop boundary
    2. Energy (average velocity) is continuous across the boundary
    3. Pitch movement is smooth at the boundary

    Args:
        score: The ScoreIR to evaluate.

    Returns:
        Score in [0.0, 1.0] where 1.0 = perfectly seamless.
    """
    notes = score.all_notes()
    if not notes:
        return 1.0

    total_beats = score.total_beats()
    if total_beats <= 0:
        return 1.0

    # Dimension 1: No notes cut off at boundary
    cutoff_score = _check_no_cutoff(notes, total_beats)

    # Dimension 2: Energy continuity
    energy_score = _check_energy_continuity(notes, total_beats)

    # Dimension 3: Pitch continuity
    pitch_score = _check_pitch_continuity(notes, total_beats)

    # Weighted average
    return 0.4 * cutoff_score + 0.3 * energy_score + 0.3 * pitch_score


def _check_no_cutoff(notes: list[Note], total_beats: float) -> float:
    """Check that no notes extend past the loop boundary.

    A note that would be cut off when the loop restarts creates
    an audible artifact.

    Args:
        notes: All notes in the score.
        total_beats: Total duration in beats.

    Returns:
        Score in [0.0, 1.0]. 1.0 = no notes cut off.
    """
    if not notes:
        return 1.0

    cutoff_count = 0
    for note in notes:
        end_beat = note.start_beat + note.duration_beats
        if end_beat > total_beats + 0.01:
            cutoff_count += 1

    if cutoff_count == 0:
        return 1.0

    # Penalize proportionally to how many notes are cut
    ratio = cutoff_count / len(notes)
    return max(0.0, 1.0 - ratio * 5.0)


def _check_energy_continuity(notes: list[Note], total_beats: float) -> float:
    """Check velocity continuity at the loop boundary.

    Compares average velocity of notes in the last beat window
    vs the first beat window.

    Args:
        notes: All notes in the score.
        total_beats: Total duration in beats.

    Returns:
        Score in [0.0, 1.0]. 1.0 = no energy jump.
    """
    window = min(4.0, total_beats * 0.25)

    end_notes = [n for n in notes if n.start_beat >= total_beats - window]
    start_notes = [n for n in notes if n.start_beat < window]

    if not end_notes or not start_notes:
        return 1.0

    end_avg_vel = sum(n.velocity for n in end_notes) / len(end_notes)
    start_avg_vel = sum(n.velocity for n in start_notes) / len(start_notes)

    diff = abs(end_avg_vel - start_avg_vel)
    # A diff of 0 = perfect, 40+ = bad
    return max(0.0, 1.0 - diff / 40.0)


def _check_pitch_continuity(notes: list[Note], total_beats: float) -> float:
    """Check pitch continuity at the loop boundary.

    Measures interval between the last sounding note and the first
    sounding note. Large leaps create jarring loop points.

    Args:
        notes: All notes in the score.
        total_beats: Total duration in beats.

    Returns:
        Score in [0.0, 1.0]. 1.0 = smooth pitch transition.
    """
    if not notes:
        return 1.0

    # Find last note (by start_beat)
    last_note = max(notes, key=lambda n: n.start_beat)
    # Find first note
    first_note = min(notes, key=lambda n: n.start_beat)

    interval = abs(last_note.pitch - first_note.pitch)

    # Intervals <= 7 semitones (perfect fifth) are fine
    if interval <= 7:
        return 1.0
    # Up to 12 (octave) is acceptable
    if interval <= 12:
        return 0.8
    # Beyond an octave, penalize
    return max(0.0, 1.0 - (interval - 7) / 24.0)
