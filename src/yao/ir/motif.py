"""Motif data structures and transformations.

A motif is the smallest musically meaningful unit — a short melodic/rhythmic
fragment that can be developed through standard transformations (transposition,
inversion, retrograde, augmentation, diminution).

PROJECT.md §5.1: Composer Subagent generates motifs as the seeds of a composition.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from yao.ir.note import Note
from yao.types import MidiNote


@dataclass(frozen=True)
class Motif:
    """A short musical fragment that serves as thematic material.

    Attributes:
        notes: Immutable tuple of notes forming the motif.
        label: Human-readable label (e.g., "main_theme", "bridge_motif").
        transformations_applied: Record of transformations applied to
            derive this motif from an original.
    """

    notes: tuple[Note, ...]
    label: str = ""
    transformations_applied: tuple[str, ...] = ()

    @property
    def duration_beats(self) -> float:
        """Total duration of the motif in beats."""
        if not self.notes:
            return 0.0
        start = min(n.start_beat for n in self.notes)
        end = max(n.end_beat() for n in self.notes)
        return end - start

    @property
    def pitch_range(self) -> tuple[MidiNote, MidiNote]:
        """Return (lowest, highest) pitch in the motif."""
        if not self.notes:
            return (0, 0)
        pitches = [n.pitch for n in self.notes]
        return (min(pitches), max(pitches))


def transpose(motif: Motif, semitones: int) -> Motif:
    """Transpose all notes by a number of semitones.

    Args:
        motif: The motif to transpose.
        semitones: Number of semitones (positive=up, negative=down).

    Returns:
        A new Motif with transposed pitches.
    """
    new_notes = tuple(replace(note, pitch=note.pitch + semitones) for note in motif.notes)
    return Motif(
        notes=new_notes,
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"transpose({semitones})"),
    )


def invert(motif: Motif, axis: MidiNote | None = None) -> Motif:
    """Invert the motif around an axis pitch.

    Melodic inversion reflects intervals: if the original goes up a 3rd,
    the inversion goes down a 3rd.

    Args:
        motif: The motif to invert.
        axis: The pitch around which to invert. If None, uses the first note's pitch.

    Returns:
        A new Motif with inverted pitches.
    """
    if not motif.notes:
        return motif

    if axis is None:
        axis = motif.notes[0].pitch

    new_notes = tuple(replace(note, pitch=2 * axis - note.pitch) for note in motif.notes)
    return Motif(
        notes=new_notes,
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"invert(axis={axis})"),
    )


def retrograde(motif: Motif) -> Motif:
    """Reverse the temporal order of notes.

    Pitches stay with their durations, but the time positions are reversed
    so the last note plays first.

    Args:
        motif: The motif to retrograde.

    Returns:
        A new Motif with reversed note order.
    """
    if len(motif.notes) <= 1:
        return motif

    start = min(n.start_beat for n in motif.notes)

    reversed_notes: list[Note] = []
    sorted_notes = sorted(motif.notes, key=lambda n: n.start_beat, reverse=True)

    current_beat = start
    for note in sorted_notes:
        reversed_notes.append(replace(note, start_beat=current_beat))
        current_beat += note.duration_beats

    return Motif(
        notes=tuple(reversed_notes),
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, "retrograde"),
    )


def augment(motif: Motif, factor: float = 2.0) -> Motif:
    """Stretch note durations by a factor (rhythmic augmentation).

    Args:
        motif: The motif to augment.
        factor: Duration multiplier (>1.0 = longer, <1.0 = shorter).

    Returns:
        A new Motif with stretched durations.
    """
    if not motif.notes:
        return motif

    base_start = min(n.start_beat for n in motif.notes)

    new_notes = tuple(
        replace(
            note,
            start_beat=base_start + (note.start_beat - base_start) * factor,
            duration_beats=note.duration_beats * factor,
        )
        for note in motif.notes
    )
    return Motif(
        notes=new_notes,
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"augment({factor})"),
    )


def diminish(motif: Motif, factor: float = 2.0) -> Motif:
    """Compress note durations by a factor (rhythmic diminution).

    Args:
        motif: The motif to diminish.
        factor: Duration divisor (>1.0 = shorter).

    Returns:
        A new Motif with compressed durations.
    """
    return augment(motif, 1.0 / factor)
