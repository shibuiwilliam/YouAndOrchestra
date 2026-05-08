"""Reharmonization Engine — 12 harmonic transformation operations.

All operations are pure functions ``(progression, position) -> progression``
with style-specific applicability rules. A ``ReharmonizationConstraints``
object ensures that reharmonized chords remain melody-compatible.

Belongs to Layer 2.5 (Combination & Coupling).

See IMPROVEMENT.md §5.1, PROJECT.md §3.4.3, CLAUDE.md Phase 3.5 Step 5.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from yao.constants.music import CHORD_INTERVALS
from yao.ir.harmony import ChordFunction


class ReharmonizationOperation(StrEnum):
    """The 12 reharmonization operations."""

    SECONDARY_DOMINANT = "secondary_dominant"
    TRITONE_SUBSTITUTION = "tritone_substitution"
    DIATONIC_SUBSTITUTION = "diatonic_substitution"
    MODAL_INTERCHANGE = "modal_interchange"
    EXTENSION_ADD = "extension_add"
    SUS_CHORD = "sus_chord"
    CHROMATIC_APPROACH = "chromatic_approach"
    II_V_INSERTION = "ii_V_insertion"
    BACKDOOR_PROGRESSION = "backdoor"
    NEAPOLITAN = "neapolitan"
    AUGMENTED_SIXTH = "augmented_sixth"
    COLTRANE_CHANGES = "coltrane_changes"


@dataclass(frozen=True)
class ReharmonizationConstraints:
    """Constraints ensuring reharmonization preserves melody compatibility.

    Attributes:
        melody_pitches_per_position: Map from position index to set of MIDI
            pitch classes sounding at that position.
        preserve_melody: If True, melody must be bit-identical after reharm.
        min_alignment: Minimum melody-harmony alignment score to accept.
    """

    melody_pitches_per_position: dict[int, frozenset[int]] = field(default_factory=dict)
    preserve_melody: bool = True
    min_alignment: float = 0.65

    def melody_compatible(
        self,
        chord_root_pc: int,
        chord_quality: str,
        position: int,
    ) -> bool:
        """Check if a chord is compatible with the melody at a position.

        A chord is compatible if no melody pitch at that position is an
        avoid note for the chord.

        Args:
            chord_root_pc: Pitch class of the chord root (0-11).
            chord_quality: Chord quality string.
            position: Position index in the progression.

        Returns:
            True if the chord is melody-compatible.
        """
        melody_pcs = self.melody_pitches_per_position.get(position)
        if melody_pcs is None:
            return True  # no melody at this position → always compatible

        chord_intervals = CHORD_INTERVALS.get(chord_quality, (0, 4, 7))
        chord_pcs = {(chord_root_pc + iv) % 12 for iv in chord_intervals}

        # A melody pitch clashes if it is a minor 2nd (1 semitone) from a chord tone
        # AND falls on this position (which is presumably a strong beat)
        for mpc in melody_pcs:
            # Check for minor 9th / minor 2nd clash
            for cpc in chord_pcs:
                if abs(mpc - cpc) % 12 == 1 and mpc not in chord_pcs:
                    return False

        return True


# Diatonic substitution map: degree -> substitute degree (third relation)
_DIATONIC_SUBS: dict[int, int] = {
    0: 2,  # I -> iii
    2: 0,  # iii -> I
    3: 5,  # IV -> vi
    5: 3,  # vi -> IV
    4: 2,  # V -> iii (less common)
    1: 3,  # ii -> IV
}


def reharmonize(
    progression: list[ChordFunction],
    operations: list[ReharmonizationOperation],
    intensity: float,
    style: str,
    constraints: ReharmonizationConstraints,
    rng: random.Random,
) -> list[ChordFunction]:
    """Apply reharmonization operations to a chord progression.

    Each position has a probability (``intensity``) of being reharmonized.
    Operations are checked for style applicability and melody compatibility
    before being applied. Operations that fail compatibility are rejected.

    This function never mutates its inputs — returns a new list.

    Args:
        progression: Input chord progression.
        operations: List of allowed operations.
        intensity: Probability of applying an operation at each position (0.0-1.0).
        style: Style context (e.g., "jazz", "classical", "gospel").
        constraints: Melody compatibility constraints.
        rng: Random number generator.

    Returns:
        A new chord progression with reharmonization applied.
    """
    result = list(progression)  # shallow copy — individual ChordFunctions are frozen

    for position in range(len(result)):
        if rng.random() > intensity:
            continue

        # Filter to applicable operations
        applicable = [op for op in operations if _is_applicable(op, result, position, style)]
        if not applicable:
            continue

        candidate_op = rng.choice(applicable)
        proposed = _apply_operation(candidate_op, result, position)

        if proposed is None:
            continue

        # Check melody compatibility
        proposed_chord = proposed[position]
        proposed_root_pc = proposed_chord.degree  # degree as pitch class proxy
        proposed_quality = proposed_chord.quality

        if not constraints.melody_compatible(proposed_root_pc, proposed_quality, position):
            continue

        result = proposed

    return result


def _is_applicable(
    operation: ReharmonizationOperation,
    progression: list[ChordFunction],
    position: int,
    style: str,
) -> bool:
    """Check if an operation is applicable at a position.

    Args:
        operation: The operation to check.
        progression: Current progression.
        position: Position index.
        style: Style context.

    Returns:
        True if the operation can be applied here.
    """
    chord = progression[position]

    if operation == ReharmonizationOperation.TRITONE_SUBSTITUTION:
        # Only on dominant chords
        return chord.quality in ("dom7", "maj")

    if operation == ReharmonizationOperation.SECONDARY_DOMINANT:
        # Need a following chord to target
        return position < len(progression) - 1

    if operation == ReharmonizationOperation.II_V_INSERTION:
        # Need a following chord and not already at the end
        return position < len(progression) - 1

    if operation == ReharmonizationOperation.MODAL_INTERCHANGE:
        # On major-quality chords
        return chord.quality in ("maj", "maj7")

    if operation == ReharmonizationOperation.EXTENSION_ADD:
        # On triads (extend to 7th)
        return chord.quality in ("maj", "min", "dim", "aug")

    if operation == ReharmonizationOperation.SUS_CHORD:
        # On dominant or major chords
        return chord.quality in ("dom7", "maj", "maj7")

    if operation == ReharmonizationOperation.BACKDOOR_PROGRESSION:
        # Replace V with bVII
        return chord.quality in ("dom7",) and position < len(progression) - 1

    if operation == ReharmonizationOperation.NEAPOLITAN:
        return True  # Can be inserted anywhere as a substitute

    if operation == ReharmonizationOperation.COLTRANE_CHANGES:
        return style in ("jazz", "post_bop", "bebop") and position + 2 < len(progression)

    # Default: applicable
    return True


def _apply_operation(
    operation: ReharmonizationOperation,
    progression: list[ChordFunction],
    position: int,
) -> list[ChordFunction] | None:
    """Apply a single reharmonization operation.

    Returns a new progression, or None if the operation cannot be applied.

    Args:
        operation: Operation to apply.
        progression: Current progression.
        position: Position index.

    Returns:
        New progression with the operation applied, or None.
    """
    result = list(progression)
    chord = result[position]

    if operation == ReharmonizationOperation.EXTENSION_ADD:
        quality_map = {"maj": "maj7", "min": "min7", "dim": "dim7", "aug": "aug"}
        new_quality = quality_map.get(chord.quality)
        if new_quality is None:
            return None
        result[position] = ChordFunction(
            degree=chord.degree,
            quality=new_quality,
            inversion=chord.inversion,
            applied_to=chord.applied_to,
        )
        return result

    if operation == ReharmonizationOperation.TRITONE_SUBSTITUTION:
        # bII7 for V7: degree moves +6 semitones (tritone)
        new_degree = (chord.degree + 6) % 7  # approximate in diatonic
        result[position] = ChordFunction(
            degree=new_degree,
            quality="dom7",
            inversion=chord.inversion,
        )
        return result

    if operation == ReharmonizationOperation.MODAL_INTERCHANGE:
        # IV -> iv (major to minor)
        quality_swap = {"maj": "min", "maj7": "min7"}
        new_quality = quality_swap.get(chord.quality)
        if new_quality is None:
            return None
        result[position] = ChordFunction(
            degree=chord.degree,
            quality=new_quality,
            inversion=chord.inversion,
        )
        return result

    if operation == ReharmonizationOperation.DIATONIC_SUBSTITUTION:
        sub_degree = _DIATONIC_SUBS.get(chord.degree)
        if sub_degree is None:
            return None
        result[position] = ChordFunction(
            degree=sub_degree,
            quality=chord.quality,
            inversion=chord.inversion,
        )
        return result

    if operation == ReharmonizationOperation.SUS_CHORD:
        result[position] = ChordFunction(
            degree=chord.degree,
            quality="sus4",
            inversion=chord.inversion,
        )
        return result

    if operation == ReharmonizationOperation.SECONDARY_DOMINANT:
        if position >= len(progression) - 1:
            return None
        target = progression[position + 1]
        # V/target: degree is 5th above target (in scale degrees, +4)
        new_degree = (target.degree + 4) % 7
        result[position] = ChordFunction(
            degree=new_degree,
            quality="dom7",
            applied_to=target.degree,
        )
        return result

    if operation == ReharmonizationOperation.BACKDOOR_PROGRESSION:
        # bVII7 -> I: replace with degree 6 (bVII approx)
        result[position] = ChordFunction(
            degree=6,
            quality="dom7",
        )
        return result

    if operation == ReharmonizationOperation.NEAPOLITAN:
        # bII chord
        result[position] = ChordFunction(
            degree=1,  # bII (approximate in diatonic)
            quality="maj",
            inversion=1,  # typically in first inversion
        )
        return result

    if operation == ReharmonizationOperation.CHROMATIC_APPROACH:
        # Insert a chord a half-step above approaching the current
        result[position] = ChordFunction(
            degree=(chord.degree + 1) % 7,
            quality="dom7",
        )
        return result

    if operation == ReharmonizationOperation.AUGMENTED_SIXTH:
        # Augmented sixth chord (approximated)
        result[position] = ChordFunction(
            degree=5,  # on b6 (approximate)
            quality="aug",
        )
        return result

    if operation == ReharmonizationOperation.COLTRANE_CHANGES:
        # Major third cycle (approximate with degree jumps)
        result[position] = ChordFunction(
            degree=(chord.degree + 4) % 7,
            quality="maj7",
        )
        return result

    if operation == ReharmonizationOperation.II_V_INSERTION:
        if position >= len(progression) - 1:
            return None
        target = progression[position + 1]
        # Replace current with ii of target
        new_degree = (target.degree + 1) % 7
        result[position] = ChordFunction(
            degree=new_degree,
            quality="min7",
            applied_to=target.degree,
        )
        return result

    return None
