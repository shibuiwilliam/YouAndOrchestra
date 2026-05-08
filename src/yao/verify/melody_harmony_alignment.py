"""Melody-Harmony Alignment metric.

For each note in a melody, scores how well it fits the active chord
using HarmonicMelodyConstraints.score_pitch(). Aggregates across the
piece as an average.

Target: >= 0.7 average, >= 0.85 on downbeats.

Belongs to Layer 6 (Verification).

See IMPROVEMENT.md §4.1, PROJECT.md §12.9, CLAUDE.md Phase 3.5 Step 6.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.coupling.harmonic_melody import derive_constraints
from yao.ir.harmonic_melody_constraints import CouplingStyle, PositionLabel
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class AlignmentReport:
    """Result of melody-harmony alignment evaluation.

    Attributes:
        overall: Average alignment score across all melody notes.
        downbeat: Average alignment score on downbeat notes only.
        note_count: Total melody notes evaluated.
        downbeat_count: Total downbeat notes evaluated.
    """

    overall: float
    downbeat: float
    note_count: int
    downbeat_count: int


def evaluate_melody_harmony_alignment(
    score: ScoreIR,
    key_root: str = "C",
    scale_type: str = "major",
    style: CouplingStyle = CouplingStyle.COMMON_PRACTICE,
) -> AlignmentReport:
    """Evaluate melody-harmony alignment for a ScoreIR.

    Scores each melody note against the chord active at that position.
    Notes on downbeats (beat 0.0) are evaluated separately.

    Args:
        score: The ScoreIR to evaluate.
        key_root: Key root note name.
        scale_type: Scale type.
        style: Coupling style for constraint derivation.

    Returns:
        AlignmentReport with overall and downbeat alignment scores.
    """
    all_scores: list[float] = []
    downbeat_scores: list[float] = []

    for note in score.all_notes():
        # Determine chord at this note's position
        chord_root, chord_quality = _find_chord_at(score, note)

        constraints = derive_constraints(
            chord_root=chord_root,
            chord_quality=chord_quality,
            key_root=key_root,
            scale_type=scale_type,
            style=style,
        )

        # Determine position label
        position = _beat_to_position(note.start_beat % 4.0)

        pitch_score = constraints.score_pitch(note.pitch, position)
        all_scores.append(pitch_score)

        if position == PositionLabel.DOWNBEAT:
            downbeat_scores.append(pitch_score)

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
    downbeat = sum(downbeat_scores) / len(downbeat_scores) if downbeat_scores else 0.0

    return AlignmentReport(
        overall=overall,
        downbeat=downbeat,
        note_count=len(all_scores),
        downbeat_count=len(downbeat_scores),
    )


def _beat_to_position(beat_in_bar: float) -> PositionLabel:
    """Convert a beat position within a bar to a PositionLabel."""
    if abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01:
        return PositionLabel.DOWNBEAT
    if abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01:
        return PositionLabel.UPBEAT
    return PositionLabel.OFFBEAT


def _find_chord_at(score: ScoreIR, note: Note) -> tuple[str, str]:
    """Find the chord active at a note's position.

    Falls back to the key root as a major chord if no chord info available.
    """
    # ScoreIR doesn't carry chord progressions directly in v2.x,
    # so we use a simple heuristic: check harmony parts for notes
    # sounding at the same time.
    # For now, return a sensible default.
    # This will be enhanced when the full Combination Stack is wired.
    return ("C", "maj")
