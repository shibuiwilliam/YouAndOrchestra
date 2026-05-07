"""Skeleton IR types for the phrase-first melody pipeline.

A skeleton is a sequence of structural pitches that anchor the melody
to the harmony. Skeleton notes are chord tones or voice-leading targets
placed at metrically important positions.

See PROJECT.md §3.2 (Layer M2) and IMPROVEMENT.md §4.1.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.types import Beat, MidiNote


@dataclass(frozen=True)
class SkeletonNote:
    """A structural pitch in the melody skeleton.

    Attributes:
        bar: Bar number (0-indexed).
        beat: Beat position within the bar.
        midi_pitch: MIDI pitch number (0–127).
        chord_relation: Relationship to the current chord
            ('root', '3rd', '5th', '7th', '9th', 'tension', 'avoid').
        structural_role: Role in the phrase structure
            ('phrase_start', 'climax', 'cadence_target', 'pivot', 'passing').
        phrase_id: Index of the phrase this note belongs to.
    """

    bar: int
    beat: Beat
    midi_pitch: MidiNote
    chord_relation: str = "root"
    structural_role: str = "passing"
    phrase_id: int = 0

    @property
    def absolute_beat(self) -> Beat:
        """Return absolute beat position (assuming 4/4 time)."""
        return self.bar * 4.0 + self.beat


@dataclass(frozen=True)
class Skeleton:
    """A sequence of skeleton notes forming the structural backbone of a melody.

    The skeleton is the output of Layer M2 and the primary input to
    Layer M3 (Surface Realization).

    Attributes:
        notes: Ordered tuple of skeleton notes.
        target_pitches: Mapping of bar number to phrase target pitch.
    """

    notes: tuple[SkeletonNote, ...]
    target_pitches: dict[int, MidiNote] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Initialize target_pitches if not provided."""
        if self.target_pitches is None:
            object.__setattr__(self, "target_pitches", {})

    @property
    def note_count(self) -> int:
        """Number of skeleton notes."""
        return len(self.notes)

    @property
    def pitch_range(self) -> tuple[MidiNote, MidiNote]:
        """Return (lowest, highest) pitch in the skeleton."""
        if not self.notes:
            return (0, 0)
        pitches = [n.midi_pitch for n in self.notes]
        return (min(pitches), max(pitches))
