"""Tuning — cents-based pitch conversions for microtonal support.

All cents/pitch conversions MUST go through this module (CLAUDE.md F5).
This prevents the ``pitch % 12`` assumption from breaking microtonal scales.

Belongs to Layer 3 (IR), alongside ScoreIR.
"""

from __future__ import annotations

# ScaleDefinition lives in constants (Layer 0) so it can be used by both
# constants/scales.py and ir/tuning.py without circular imports.
from yao.constants.scales import ScaleDefinition as ScaleDefinition  # noqa: F401 — re-export


class Tuning:
    """Cents-based pitch conversion utilities.

    Replaces raw ``pitch % 12`` for microtonal safety.
    All methods are static — no state.
    """

    @staticmethod
    def cents_from_a4(midi_pitch: int, cents_offset: float = 0.0) -> float:
        """Convert MIDI pitch + cents offset to absolute cents from A4.

        A4 = MIDI 69 = 0 cents. Each 12-EDO semitone = 100 cents.

        Args:
            midi_pitch: MIDI note number (0-127).
            cents_offset: Additional cents offset (for microtonal detuning).

        Returns:
            Absolute cents from A4.
        """
        return (midi_pitch - 69) * 100.0 + cents_offset

    @staticmethod
    def midi_from_cents(cents_from_a4: float) -> tuple[int, float]:
        """Convert cents from A4 to nearest MIDI note + bend offset.

        Args:
            cents_from_a4: Absolute cents from A4.

        Returns:
            Tuple of (nearest_midi_note, bend_cents) where
            bend_cents is in [-50.0, +50.0).
        """
        semitones = cents_from_a4 / 100.0
        midi = round(69 + semitones)
        midi = max(0, min(127, midi))
        bend = cents_from_a4 - (midi - 69) * 100.0
        return (midi, bend)

    @staticmethod
    def pitch_bend_from_cents(
        cents: float,
        bend_range_semitones: int = 2,
    ) -> int:
        """Convert cents offset to MIDI pitch bend value.

        Args:
            cents: Offset in cents.
            bend_range_semitones: Pitch bend range in semitones (default 2).

        Returns:
            MIDI pitch bend value in [-8192, +8191].
        """
        max_cents = bend_range_semitones * 100.0
        if max_cents <= 0:
            return 0
        normalized = cents / max_cents
        return max(-8192, min(8191, round(normalized * 8192)))

    @staticmethod
    def scale_pitches_cents(
        root_midi: int,
        scale: ScaleDefinition,
        octaves: int = 1,
    ) -> list[tuple[int, float]]:
        """Generate (midi_note, cents_offset) pairs for a scale.

        For 12-EDO scales, cents_offset is always 0.0.
        For microtonal scales, cents_offset is the deviation from
        the nearest 12-EDO semitone.

        Args:
            root_midi: MIDI note number of the root.
            scale: Scale definition with cents intervals.
            octaves: Number of octaves to generate.

        Returns:
            List of (midi_note, cents_offset) tuples.
        """
        root_cents = Tuning.cents_from_a4(root_midi)
        result: list[tuple[int, float]] = []

        for octave in range(octaves):
            octave_offset = octave * scale.octave_cents
            for interval_cents in scale.intervals_cents:
                total_cents = root_cents + octave_offset + interval_cents
                midi, bend = Tuning.midi_from_cents(total_cents)
                result.append((midi, bend))

        return result

    @staticmethod
    def pitch_class_cents(midi_pitch: int, cents_offset: float = 0.0) -> float:
        """Get the pitch class in cents within one octave.

        Microtonal-safe replacement for ``midi_pitch % 12``.

        Args:
            midi_pitch: MIDI note number.
            cents_offset: Additional cents offset.

        Returns:
            Pitch class in cents [0, octave_cents).
        """
        total_cents = (midi_pitch % 12) * 100.0 + cents_offset
        return total_cents % 1200.0
