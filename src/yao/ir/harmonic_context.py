"""HarmonicContext — harmonic state at a given metric position.

The HarmonicContext provides the harmonic information that Layer M2
(Skeleton Generation) needs to select chord-tone targets and
voice-leading paths.

See IMPROVEMENT.md §4.4 and PROJECT.md §5.2.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.constants.music import CHORD_INTERVALS
from yao.ir.notation import note_name_to_midi
from yao.types import Beat, MidiNote


@dataclass(frozen=True)
class HarmonicContext:
    """Harmonic state at a specific metric position.

    Provides the chord tones, available tensions, and voice-leading
    targets needed by the skeleton generator to make harmonically
    informed pitch decisions.

    Attributes:
        bar: Bar number (0-indexed).
        beat: Beat position within the bar.
        chord_root: Root note name (e.g., "C", "F#").
        chord_quality: Chord quality (e.g., "maj", "min", "dom7", "maj7").
        next_chord_root: Root of the next chord, or None.
        next_chord_quality: Quality of the next chord, or None.
        scale_name: Active scale name for this position.
        metric_position: Metric strength (0.0 = downbeat, 1.0 = weakest).
    """

    bar: int
    beat: Beat
    chord_root: str
    chord_quality: str = "maj"
    next_chord_root: str | None = None
    next_chord_quality: str | None = None
    scale_name: str = "major"
    metric_position: float = 0.0

    @property
    def chord_tones(self) -> tuple[int, ...]:
        """Return the intervals (in semitones from root) of the chord tones.

        Uses CHORD_INTERVALS from constants for the chord quality.
        """
        intervals = CHORD_INTERVALS.get(self.chord_quality)
        if intervals is None:
            # Fallback to major triad if quality is unknown
            return (0, 4, 7)
        return tuple(intervals)

    def chord_tone_pitches(self, octave: int = 4) -> tuple[MidiNote, ...]:
        """Return absolute MIDI pitches for the chord tones.

        Args:
            octave: Octave to realize the chord in.

        Returns:
            Tuple of MIDI note numbers.
        """
        root_midi = note_name_to_midi(f"{self.chord_root}{octave}")
        return tuple(root_midi + interval for interval in self.chord_tones)

    def is_chord_tone(self, midi_pitch: MidiNote) -> bool:
        """Check if a MIDI pitch is a chord tone (any octave).

        Args:
            midi_pitch: MIDI note number to check.

        Returns:
            True if the pitch class matches a chord tone.
        """
        root_midi = note_name_to_midi(f"{self.chord_root}4")
        pitch_class_offset = (midi_pitch - root_midi) % 12
        return pitch_class_offset in self.chord_tones

    def voice_leading_targets(self, octave: int = 4) -> tuple[MidiNote, ...]:
        """Return good voice-leading targets toward the next chord.

        Prefers smooth (half-step or whole-step) motion to the
        next chord's tones.

        Args:
            octave: Octave to realize pitches in.

        Returns:
            Tuple of MIDI note numbers that are good transition targets.
            Empty if there is no next chord.
        """
        if self.next_chord_root is None:
            return ()
        next_quality = self.next_chord_quality or "maj"
        next_intervals = CHORD_INTERVALS.get(next_quality, [0, 4, 7])
        next_root_midi = note_name_to_midi(f"{self.next_chord_root}{octave}")
        return tuple(next_root_midi + interval for interval in next_intervals)
