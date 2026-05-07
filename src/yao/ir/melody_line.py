"""MelodyLine IR types for the phrase-first melody pipeline.

A MelodyLine is a sequence of realized melody notes that connect skeleton
notes via passing tones, neighbor tones, and other surface decorations.
An OrnamentedNote extends a MelodyNote with expressive details.

See PROJECT.md §3.2 (Layers M3 and M4) and IMPROVEMENT.md §4.1.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.types import Beat, MidiNote, Velocity


@dataclass(frozen=True)
class MelodyNote:
    """A single note in the realized melody surface.

    Attributes:
        bar: Bar number (0-indexed).
        beat: Beat position within the bar.
        duration_beats: Duration in beats.
        midi_pitch: MIDI pitch number (0–127).
        velocity: MIDI velocity (0–127).
        note_type: Classification of this note's function
            ('chord_tone', 'passing', 'neighbor', 'appoggiatura',
             'escape', 'anticipation', 'ghost').
        skeleton_id: Index of the skeleton note this surface note
            decorates, or None if not directly connected.
    """

    bar: int
    beat: Beat
    duration_beats: Beat
    midi_pitch: MidiNote
    velocity: Velocity = 80
    note_type: str = "chord_tone"
    skeleton_id: int | None = None

    @property
    def absolute_beat(self) -> Beat:
        """Return absolute beat position (assuming 4/4 time)."""
        return self.bar * 4.0 + self.beat

    @property
    def end_beat(self) -> Beat:
        """Return the beat position where this note ends (within bar)."""
        return self.beat + self.duration_beats


@dataclass(frozen=True)
class OrnamentedNote:
    """A melody note with expressive ornament and articulation details.

    Extends the MelodyNote concept with Layer M4 additions: ornaments,
    articulation, microtiming offsets, and velocity modifiers.

    Attributes:
        bar: Bar number (0-indexed).
        beat: Beat position within the bar.
        duration_beats: Duration in beats.
        midi_pitch: MIDI pitch number (0–127).
        velocity: MIDI velocity (0–127).
        note_type: Classification of this note's function.
        skeleton_id: Index of the skeleton note this decorates.
        ornaments: Tuple of ornament names applied to this note.
        articulation: Articulation marking.
        micro_timing_offset_ms: Groove-derived timing shift in ms.
        velocity_modifier: Multiplicative velocity adjustment.
    """

    bar: int
    beat: Beat
    duration_beats: Beat
    midi_pitch: MidiNote
    velocity: Velocity = 80
    note_type: str = "chord_tone"
    skeleton_id: int | None = None
    ornaments: tuple[str, ...] = ()
    articulation: str = "normal"
    micro_timing_offset_ms: float = 0.0
    velocity_modifier: float = 1.0

    @property
    def absolute_beat(self) -> Beat:
        """Return absolute beat position (assuming 4/4 time)."""
        return self.bar * 4.0 + self.beat

    @property
    def effective_velocity(self) -> int:
        """Return velocity after applying the modifier, clamped to [0, 127]."""
        return max(0, min(127, int(self.velocity * self.velocity_modifier)))


@dataclass(frozen=True)
class MelodyLine:
    """A complete realized melody as a sequence of notes.

    The MelodyLine is the output of Layer M3 (Surface Realization)
    and the input to Layer M4 (Ornament & Articulation).

    Attributes:
        notes: Ordered tuple of melody notes.
    """

    notes: tuple[MelodyNote, ...]

    @property
    def note_count(self) -> int:
        """Number of notes in the melody."""
        return len(self.notes)

    @property
    def pitch_range(self) -> tuple[MidiNote, MidiNote]:
        """Return (lowest, highest) pitch in the melody."""
        if not self.notes:
            return (0, 0)
        pitches = [n.midi_pitch for n in self.notes]
        return (min(pitches), max(pitches))


@dataclass(frozen=True)
class OrnamentedMelodyLine:
    """A complete melody with ornaments and articulation applied.

    The output of Layer M4 (Ornament & Articulation) and the final
    melodic product of the phrase-first pipeline.

    Attributes:
        notes: Ordered tuple of ornamented notes.
    """

    notes: tuple[OrnamentedNote, ...]

    @property
    def note_count(self) -> int:
        """Number of notes in the ornamented melody."""
        return len(self.notes)

    @property
    def pitch_range(self) -> tuple[MidiNote, MidiNote]:
        """Return (lowest, highest) pitch in the melody."""
        if not self.notes:
            return (0, 0)
        pitches = [n.midi_pitch for n in self.notes]
        return (min(pitches), max(pitches))
