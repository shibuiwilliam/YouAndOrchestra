"""Harmonic-Melodic Coupling — derive melody constraints from chords.

This module implements the ``derive_constraints()`` function that produces
``HarmonicMelodyConstraints`` for a given chord, key, scale type, and
coupling style. The constraints are consumed by Layer M2 (Skeleton
Generation) to make harmonically informed pitch decisions.

Belongs to Layer 2.5 (Combination & Coupling).
Imports allowed: Layers 0 (constants), 1 (schema, ir).

See IMPROVEMENT.md §4.1, PROJECT.md §3.4.1, CLAUDE.md Phase 3.5 Step 2.
"""

from __future__ import annotations

from functools import lru_cache

from yao.constants.music import CHORD_INTERVALS, NOTE_NAMES, SCALE_INTERVALS
from yao.ir.harmonic_melody_constraints import (
    CouplingStyle,
    HarmonicMelodyConstraints,
)


def derive_constraints(
    chord_root: str,
    chord_quality: str,
    key_root: str,
    scale_type: str,
    style: CouplingStyle,
) -> HarmonicMelodyConstraints:
    """Derive melody constraints from a chord event.

    Computes which pitch classes are chord tones, available extensions,
    avoid notes, and target resolutions based on the chord, key, and
    coupling style.

    Results are cached per unique combination of arguments for the
    duration of the generation pass (<5ms per chord, per CLAUDE.md
    performance budget).

    Args:
        chord_root: Root note name of the chord (e.g., "C", "F#", "Bb").
        chord_quality: Chord quality (e.g., "maj", "min7", "dom7").
        key_root: Root note name of the current key (e.g., "C", "G").
        scale_type: Scale type (e.g., "major", "minor", "dorian").
        style: Coupling style governing constraint strictness.

    Returns:
        A frozen HarmonicMelodyConstraints with absolute pitch classes.
    """
    return _derive_cached(chord_root, chord_quality, key_root, scale_type, style)


@lru_cache(maxsize=256)
def _derive_cached(
    chord_root: str,
    chord_quality: str,
    key_root: str,
    scale_type: str,
    style: CouplingStyle,
) -> HarmonicMelodyConstraints:
    """Cached implementation of derive_constraints."""
    # Resolve chord root to pitch class
    root_pc = _note_to_pitch_class(chord_root)

    # Get chord intervals and convert to absolute pitch classes
    chord_intervals = CHORD_INTERVALS.get(chord_quality, (0, 4, 7))
    chord_tone_pcs = tuple((root_pc + interval) % 12 for interval in chord_intervals)

    # Get scale pitch classes
    scale_intervals = SCALE_INTERVALS.get(scale_type, SCALE_INTERVALS["major"])
    key_pc = _note_to_pitch_class(key_root)
    scale_pcs = frozenset((key_pc + interval) % 12 for interval in scale_intervals)

    # Derive style-specific rules
    rules = _STYLE_RULES[style]
    avoid_pcs = rules.compute_avoid_notes(root_pc, chord_quality, chord_tone_pcs, scale_pcs)
    extension_pcs = rules.compute_extensions(root_pc, chord_quality, chord_tone_pcs, scale_pcs, avoid_pcs)
    resolutions = rules.compute_resolutions(root_pc, chord_quality, chord_tone_pcs, key_pc, scale_pcs)

    return HarmonicMelodyConstraints(
        chord_tones=chord_tone_pcs,
        available_extensions=extension_pcs,
        avoid_notes=avoid_pcs,
        target_resolutions=resolutions,
        style=style,
    )


def clear_cache() -> None:
    """Clear the constraints cache. Call between generation passes."""
    _derive_cached.cache_clear()


def _note_to_pitch_class(note_name: str) -> int:
    """Convert a note name to a pitch class (0-11).

    Handles enharmonic equivalents (Bb -> A# -> 10, etc.).
    """
    from yao.constants.music import ENHARMONIC_MAP

    normalized = note_name[0].upper() + note_name[1:] if len(note_name) > 1 else note_name.upper()
    if normalized in ENHARMONIC_MAP:
        normalized = ENHARMONIC_MAP[normalized]
    if normalized in NOTE_NAMES:
        return NOTE_NAMES.index(normalized)
    # Fallback: try just the letter
    return NOTE_NAMES.index(normalized[0].upper()) if normalized[0].upper() in NOTE_NAMES else 0


# ---------------------------------------------------------------------------
# Style-specific rule sets
# ---------------------------------------------------------------------------


class _StyleRules:
    """Base class for coupling-style-specific avoid/extension/resolution rules.

    Each style overrides methods to customize which pitches are avoid notes,
    available extensions, and target resolutions.
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        """Compute avoid notes for this style. Default: none."""
        return ()

    def compute_extensions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
        avoid_pcs: tuple[int, ...],
    ) -> tuple[int, ...]:
        """Compute available extensions. Default: scale tones not in chord or avoid."""
        excluded = set(chord_tone_pcs) | set(avoid_pcs)
        return tuple(pc for pc in sorted(scale_pcs) if pc not in excluded)

    def compute_resolutions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        key_pc: int,
        scale_pcs: frozenset[int],
    ) -> dict[int, int]:
        """Compute target resolutions. Default: leading tone → tonic."""
        resolutions: dict[int, int] = {}
        # Leading tone resolves to tonic
        leading_tone = (key_pc - 1) % 12
        if leading_tone in scale_pcs or leading_tone in chord_tone_pcs:
            resolutions[leading_tone] = key_pc
        return resolutions


class _CommonPracticeRules(_StyleRules):
    """Common-practice voice leading rules.

    - P4 (perfect fourth above root) over major triad penalized on strong beats
    - Prefer 3rd/5th on downbeats
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        avoid: list[int] = []
        # P4 above root on major-quality chords
        if chord_quality in ("maj", "maj7", "maj9"):
            p4 = (root_pc + 5) % 12
            if p4 not in chord_tone_pcs:
                avoid.append(p4)
        return tuple(avoid)

    def compute_resolutions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        key_pc: int,
        scale_pcs: frozenset[int],
    ) -> dict[int, int]:
        resolutions = super().compute_resolutions(root_pc, chord_quality, chord_tone_pcs, key_pc, scale_pcs)
        # 7th of dominant chord resolves down to 3rd of tonic
        if chord_quality in ("dom7",):
            seventh_pc = (root_pc + 10) % 12
            # b7 resolves down by half-step
            resolutions[seventh_pc] = (seventh_pc - 1) % 12
        # 3rd of V resolves up to tonic
        if chord_quality in ("dom7", "maj"):
            third_pc = (root_pc + 4) % 12
            resolutions[third_pc] = (third_pc + 1) % 12
        return resolutions


class _JazzRules(_StyleRules):
    """Jazz voice leading rules.

    - Avoid 11th on dominant 7th chords (clashes with 3rd)
    - Extensions (9, 13) are welcomed
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        avoid: list[int] = []
        # Avoid 11th (P4) on dominant 7th and major 7th chords
        if chord_quality in ("dom7", "maj7", "maj9"):
            p4 = (root_pc + 5) % 12
            if p4 not in chord_tone_pcs:
                avoid.append(p4)
        return tuple(avoid)

    def compute_resolutions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        key_pc: int,
        scale_pcs: frozenset[int],
    ) -> dict[int, int]:
        resolutions = super().compute_resolutions(root_pc, chord_quality, chord_tone_pcs, key_pc, scale_pcs)
        # In jazz: b7 resolves to 3rd of next chord (typically down by half-step)
        if chord_quality in ("dom7",):
            seventh_pc = (root_pc + 10) % 12
            resolutions[seventh_pc] = (seventh_pc - 1) % 12
        return resolutions


class _BluesRules(_StyleRules):
    """Blues rules.

    - b3, b5, b7 are blue notes — neutral/positive, never avoid notes
    - No avoid notes at all
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        # Blues: no avoid notes — blue notes are expressive, not wrong
        return ()

    def compute_extensions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
        avoid_pcs: tuple[int, ...],
    ) -> tuple[int, ...]:
        # Include blue notes as extensions: b3, b5, b7
        blue_notes = {(root_pc + 3) % 12, (root_pc + 6) % 12, (root_pc + 10) % 12}
        base_extensions = set(super().compute_extensions(root_pc, chord_quality, chord_tone_pcs, scale_pcs, avoid_pcs))
        all_extensions = base_extensions | (blue_notes - set(chord_tone_pcs))
        return tuple(sorted(all_extensions))


class _ModalRules(_StyleRules):
    """Modal rules.

    - No avoid notes — all scale tones are equal
    - Extensions include all non-chord scale tones
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        return ()


class _RagaRules(_StyleRules):
    """Raga rules.

    - Pitch hierarchy from scale (vadi/samvadi emphasis)
    - No avoid notes — hierarchy is expressed through resolution targets
    - Target resolutions: each non-chord scale tone resolves to nearest chord tone
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        return ()

    def compute_resolutions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        key_pc: int,
        scale_pcs: frozenset[int],
    ) -> dict[int, int]:
        resolutions: dict[int, int] = {}
        chord_set = set(chord_tone_pcs)
        for pc in scale_pcs:
            if pc not in chord_set:
                # Resolve to nearest chord tone
                nearest = min(chord_tone_pcs, key=lambda ct: min(abs(pc - ct), 12 - abs(pc - ct)))
                resolutions[pc] = nearest
        return resolutions


class _MaqamRules(_StyleRules):
    """Maqam rules.

    - Similar to raga: pitch hierarchy, no avoid notes
    - Characteristic-pitch resolution patterns
    """

    def compute_avoid_notes(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        scale_pcs: frozenset[int],
    ) -> tuple[int, ...]:
        return ()

    def compute_resolutions(
        self,
        root_pc: int,
        chord_quality: str,
        chord_tone_pcs: tuple[int, ...],
        key_pc: int,
        scale_pcs: frozenset[int],
    ) -> dict[int, int]:
        resolutions: dict[int, int] = {}
        chord_set = set(chord_tone_pcs)
        for pc in scale_pcs:
            if pc not in chord_set:
                nearest = min(chord_tone_pcs, key=lambda ct: min(abs(pc - ct), 12 - abs(pc - ct)))
                resolutions[pc] = nearest
        return resolutions


# Registry of style rules — no hardcoded style selection in generators
_STYLE_RULES: dict[CouplingStyle, _StyleRules] = {
    CouplingStyle.COMMON_PRACTICE: _CommonPracticeRules(),
    CouplingStyle.JAZZ: _JazzRules(),
    CouplingStyle.BLUES: _BluesRules(),
    CouplingStyle.MODAL: _ModalRules(),
    CouplingStyle.RAGA: _RagaRules(),
    CouplingStyle.MAQAM: _MaqamRules(),
}
