"""HarmonicMelodyConstraints — chord-derived constraints for melody pitch selection.

This IR type captures the relationship between a chord and the melody pitches
that can sound above it. It is the core data structure for the Harmonic-Melodic
Coupling Layer (Layer 2.5, §4.1 in IMPROVEMENT.md).

The ``score_pitch()`` method returns a fitness score in [0.0, 1.0] for any
MIDI pitch at any metric position, allowing Layer M2 (Skeleton Generation)
to make harmonically informed pitch decisions.

Belongs to Layer 1 (IR). Consumed by Layer 2.5 (Coupling) and Layer 2
(Generation).

See IMPROVEMENT.md §4.1, PROJECT.md §3.4.1, CLAUDE.md Phase 3.5 Step 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from yao.types import MidiNote


class CouplingStyle(StrEnum):
    """How strictly melody-harmony coupling is enforced.

    Each style defines different rules for which pitches are chord tones,
    available extensions, avoid notes, and target resolutions.

    See PROJECT.md §3.4.1 for the full description of each style.
    """

    COMMON_PRACTICE = "common_practice"
    """Classical voice leading. P4 over major triad penalized on strong beats.
    Prefer 3rd/5th on downbeats."""

    JAZZ = "jazz"
    """Extensions favored. 11th over V7 penalized. Blue notes neutral."""

    BLUES = "blues"
    """b3, b5, b7 are blue notes (neutral/positive), not avoid notes."""

    MODAL = "modal"
    """No avoid notes. All scale tones equal."""

    RAGA = "raga"
    """Pitch hierarchy from TonalSystem.cadence_strength and characteristic
    pitch logic."""

    MAQAM = "maqam"
    """Pitch hierarchy from TonalSystem.cadence_strength and characteristic
    pitch logic."""


class PositionLabel(StrEnum):
    """Metric position label for pitch scoring.

    Determines how strictly constraints are applied. Strong beats
    (DOWNBEAT) are stricter; weak beats (OFFBEAT) are more tolerant.
    """

    DOWNBEAT = "downbeat"
    """Strong beat (beat 1, beat 3 in 4/4). Strictest constraint application."""

    UPBEAT = "upbeat"
    """Secondary beat (beat 2, beat 4 in 4/4). Moderate constraint application."""

    OFFBEAT = "offbeat"
    """Weak subdivision (off-beat 8ths, 16ths). Most tolerant."""

    APPROACH = "approach"
    """Approach to a target note. Resolution-aware scoring: tendency tones
    that resolve to chord tones score higher."""


# Position-dependent weight multipliers for scoring.
# Higher values = stricter enforcement of chord-tone preference.
_POSITION_WEIGHTS: dict[PositionLabel, float] = {
    PositionLabel.DOWNBEAT: 1.0,
    PositionLabel.UPBEAT: 0.7,
    PositionLabel.OFFBEAT: 0.4,
    PositionLabel.APPROACH: 0.5,
}

# Base scores for each pitch category
_CHORD_TONE_BASE: float = 1.0
_EXTENSION_BASE: float = 0.6
_PASSING_TONE_BASE: float = 0.35
_AVOID_NOTE_BASE: float = 0.05
_RESOLUTION_APPROACH_BONUS: float = 0.3


@dataclass(frozen=True)
class HarmonicMelodyConstraints:
    """Constraints derived from the current chord for melody generation.

    All pitch values are **pitch classes** (0–11, where C=0, C#=1, ..., B=11).
    The ``score_pitch()`` method accepts absolute MIDI notes and extracts
    the pitch class internally, making scoring octave-invariant.

    This dataclass is frozen (immutable) per Non-Negotiable Rule 9:
    coupling modules never mutate their inputs.

    Attributes:
        chord_tones: Pitch classes that are members of the chord (root, 3rd, 5th, 7th).
        available_extensions: Pitch classes that are acceptable tensions (9th, 11th, 13th).
        avoid_notes: Pitch classes that clash with the chord on strong beats.
        target_resolutions: Map from pitch class to its resolution target pitch class.
            E.g., {11: 0} means B resolves to C (leading tone resolution).
        style: The coupling style governing how strictly constraints are applied.
    """

    chord_tones: tuple[int, ...]
    available_extensions: tuple[int, ...]
    avoid_notes: tuple[int, ...]
    target_resolutions: dict[int, int]
    style: CouplingStyle

    def score_pitch(self, pitch: MidiNote, position: PositionLabel) -> float:
        """Score a pitch given its rhythmic position.

        Returns a fitness score in [0.0, 1.0]:
        - 1.0 = excellent fit (chord tone on downbeat)
        - ~0.6 = good fit (available extension)
        - ~0.35 = neutral (passing tone)
        - ~0.05 = poor fit (avoid note on strong beat)

        The score is modulated by metric position: strong beats enforce
        chord-tone preference more strictly; weak beats are more tolerant.

        Args:
            pitch: Absolute MIDI note number (0–127).
            position: Metric position label.

        Returns:
            Float in [0.0, 1.0]. Never returns values outside this range.
        """
        pitch_class = pitch % 12
        pos_weight = _POSITION_WEIGHTS[position]

        # Determine the base category score for this pitch class
        base_score = self._categorize_pitch(pitch_class)

        # Apply resolution bonus for approach positions
        if position == PositionLabel.APPROACH and pitch_class in self.target_resolutions:
            base_score = min(1.0, base_score + _RESOLUTION_APPROACH_BONUS)

        # Interpolate between base_score and a neutral midpoint based on position weight.
        # On strong beats (weight=1.0), the category score dominates.
        # On weak beats (weight=0.4), scores converge toward a moderate value.
        neutral = 0.5
        final_score = neutral + pos_weight * (base_score - neutral)

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, final_score))

    def _categorize_pitch(self, pitch_class: int) -> float:
        """Return the raw category score for a pitch class.

        Args:
            pitch_class: Pitch class (0–11).

        Returns:
            Raw score before position weighting.
        """
        if pitch_class in self.chord_tones:
            return _CHORD_TONE_BASE

        if pitch_class in self.avoid_notes:
            return _AVOID_NOTE_BASE

        if pitch_class in self.available_extensions:
            return _EXTENSION_BASE

        return _PASSING_TONE_BASE
