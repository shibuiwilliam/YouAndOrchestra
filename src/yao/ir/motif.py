"""Motif data structures and transformations.

A motif is the smallest musically meaningful unit — a short melodic/rhythmic
fragment that can be developed through standard transformations (transposition,
inversion, retrograde, augmentation, diminution).

PROJECT.md §5.1: Composer Subagent generates motifs as the seeds of a composition.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

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


def sequence(motif: Motif, semitones: int, repetitions: int = 2) -> Motif:
    """Create a sequential repetition by repeating with transposition.

    Each repetition is transposed by the given interval, producing a
    chain of the motif at successive pitch levels.

    Args:
        motif: The motif to sequence.
        semitones: Transposition per repetition.
        repetitions: Number of times to repeat (total copies = repetitions + 1).

    Returns:
        A new Motif containing the original followed by transposed copies.
    """
    if not motif.notes:
        return motif

    all_notes: list[Note] = list(motif.notes)
    motif_duration = motif.duration_beats

    for rep in range(1, repetitions + 1):
        time_offset = motif_duration * rep
        pitch_offset = semitones * rep
        for note in motif.notes:
            all_notes.append(
                replace(
                    note,
                    pitch=note.pitch + pitch_offset,
                    start_beat=note.start_beat + time_offset,
                )
            )

    return Motif(
        notes=tuple(all_notes),
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"sequence({semitones}x{repetitions})"),
    )


def fragment(motif: Motif, start_idx: int = 0, length: int = 2) -> Motif:
    """Extract a fragment (subset) of the motif.

    Args:
        motif: The motif to fragment.
        start_idx: Starting note index.
        length: Number of notes to extract.

    Returns:
        A new Motif containing the fragment.
    """
    if not motif.notes:
        return motif

    end_idx = min(start_idx + length, len(motif.notes))
    fragment_notes = motif.notes[start_idx:end_idx]

    if not fragment_notes:
        return motif

    # Normalize start_beat to 0
    base = fragment_notes[0].start_beat
    normalized = tuple(replace(n, start_beat=n.start_beat - base) for n in fragment_notes)

    return Motif(
        notes=normalized,
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"fragment({start_idx}:{end_idx})"),
    )


def extend(motif: Motif, extra_notes: int = 2) -> Motif:
    """Extend the motif by repeating its last notes.

    Args:
        motif: The motif to extend.
        extra_notes: Number of notes to add by continuing the pattern.

    Returns:
        A new Motif with extra notes appended.
    """
    if len(motif.notes) < 2:  # noqa: PLR2004
        return motif

    last = motif.notes[-1]
    prev = motif.notes[-2]
    interval = last.pitch - prev.pitch
    duration = last.duration_beats
    current_beat = last.start_beat + duration

    extra: list[Note] = []
    current_pitch = last.pitch
    for _ in range(extra_notes):
        current_pitch += interval
        extra.append(replace(last, pitch=current_pitch, start_beat=current_beat))
        current_beat += duration

    return Motif(
        notes=(*motif.notes, *extra),
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"extend({extra_notes})"),
    )


def truncate(motif: Motif, keep: int = 2) -> Motif:
    """Truncate the motif to its first N notes.

    Args:
        motif: The motif to truncate.
        keep: Number of notes to keep from the beginning.

    Returns:
        A new Motif with only the first N notes.
    """
    if not motif.notes or keep >= len(motif.notes):
        return motif

    return Motif(
        notes=motif.notes[:keep],
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"truncate({keep})"),
    )


def chromatic_decoration(motif: Motif) -> Motif:
    """Add chromatic neighbor notes before each note.

    Inserts a half-step approach tone before each note (from below),
    halving the original note's duration to make room.

    Args:
        motif: The motif to decorate.

    Returns:
        A new Motif with chromatic approaches inserted.
    """
    if not motif.notes:
        return motif

    decorated: list[Note] = []
    for note in motif.notes:
        approach_dur = note.duration_beats * 0.25
        main_dur = note.duration_beats * 0.75
        # Chromatic approach from below
        decorated.append(
            replace(
                note,
                pitch=note.pitch - 1,
                start_beat=note.start_beat,
                duration_beats=approach_dur,
            )
        )
        decorated.append(
            replace(
                note,
                start_beat=note.start_beat + approach_dur,
                duration_beats=main_dur,
            )
        )

    return Motif(
        notes=tuple(decorated),
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, "chromatic_decoration"),
    )


def rhythmic_displacement(motif: Motif, offset_beats: float = 0.5) -> Motif:
    """Shift the motif in time (rhythmic displacement / hemiola).

    Args:
        motif: The motif to displace.
        offset_beats: How many beats to shift forward.

    Returns:
        A new Motif shifted in time.
    """
    if not motif.notes:
        return motif

    shifted = tuple(replace(note, start_beat=note.start_beat + offset_beats) for note in motif.notes)
    return Motif(
        notes=shifted,
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, f"rhythmic_displacement({offset_beats})"),
    )


def interpolate(motif: Motif) -> Motif:
    """Insert interpolated notes between existing notes.

    Adds a note at the midpoint (pitch and time) between each pair
    of consecutive notes, creating a smoother line.

    Args:
        motif: The motif to interpolate.

    Returns:
        A new Motif with interpolated notes inserted.
    """
    if len(motif.notes) < 2:  # noqa: PLR2004
        return motif

    result: list[Note] = []
    for i in range(len(motif.notes) - 1):
        curr = motif.notes[i]
        nxt = motif.notes[i + 1]
        result.append(curr)

        # Interpolated note at midpoint
        mid_beat = (curr.start_beat + nxt.start_beat) / 2
        mid_pitch = (curr.pitch + nxt.pitch) // 2
        mid_dur = nxt.start_beat - mid_beat
        # Shorten current note to make room
        result[-1] = replace(curr, duration_beats=mid_beat - curr.start_beat)
        result.append(
            replace(
                curr,
                pitch=mid_pitch,
                start_beat=mid_beat,
                duration_beats=max(0.1, mid_dur),
            )
        )

    result.append(motif.notes[-1])

    return Motif(
        notes=tuple(result),
        label=motif.label,
        transformations_applied=(*motif.transformations_applied, "interpolate"),
    )


# All available transformations as a registry
TRANSFORMATION_REGISTRY: dict[str, object] = {
    "identity": lambda m: m,
    "transposed": transpose,
    "inverted": invert,
    "retrograde": retrograde,
    "augmented": augment,
    "diminished": diminish,
    "sequential": sequence,
    "fragmented": fragment,
    "extension": extend,
    "truncation": truncate,
    "chromatic_decoration": chromatic_decoration,
    "rhythmic_displacement": rhythmic_displacement,
    "interpolation": interpolate,
}


# ---------------------------------------------------------------------------
# Motif Network (A2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MotifNode:
    """A node in the motif evolutionary tree.

    Tracks how a motif instance relates to its parent through transformation,
    and where in the piece it appears.

    Attributes:
        motif: The motif at this node.
        parent_id: Label of the parent motif, or None if this is a seed.
        transformation: The transformation applied to derive this from its parent.
        bar_locations: Bars where this motif instance appears.
    """

    motif: Motif
    parent_id: str | None = None
    transformation: str = "identity"
    bar_locations: tuple[int, ...] = ()


@dataclass
class MotifNetwork:
    """Tracks the evolutionary tree of motifs across a piece.

    The network records which motifs appear, how they derive from each other,
    and where they are placed. This enables structural critique: "motif coverage
    is only 30%" or "all variations are transpositions — consider inversions."

    Goodhart defense: coverage_ratio can be gamed by inserting trivial
    motif fragments everywhere. Cross-check with variation_diversity
    (which requires different transformation types) and the critic's
    motif-quality checks.

    Attributes:
        nodes: Mapping from motif label/id to its MotifNode.
        total_bars: Total number of bars in the piece.
    """

    nodes: dict[str, MotifNode] = field(default_factory=dict)
    total_bars: int = 1

    def add_node(self, node: MotifNode, key: str | None = None) -> str:
        """Add a motif node to the network.

        Args:
            node: The MotifNode to add.
            key: Optional explicit key. If None, auto-generates a unique key
                from the motif label.

        Returns:
            The key under which the node was stored.
        """
        if key is None:
            base = node.motif.label or "motif"
            key = base
            counter = 0
            while key in self.nodes:
                counter += 1
                key = f"{base}_{counter}"
        self.nodes[key] = node
        return key

    def trace_lineage(self, motif_id: str) -> list[MotifNode]:
        """Trace the derivation chain from a motif back to its seed.

        Args:
            motif_id: Label of the motif to trace.

        Returns:
            List of MotifNodes from seed to the given motif.
        """
        chain: list[MotifNode] = []
        current_id: str | None = motif_id
        visited: set[str] = set()
        while current_id and current_id in self.nodes and current_id not in visited:
            visited.add(current_id)
            node = self.nodes[current_id]
            chain.append(node)
            current_id = node.parent_id
        chain.reverse()
        return chain

    def coverage_ratio(self) -> float:
        """Fraction of bars containing some motif derivative.

        Returns:
            Float in [0.0, 1.0]. 1.0 means every bar has motif material.
        """
        if self.total_bars <= 0:
            return 0.0
        covered_bars: set[int] = set()
        for node in self.nodes.values():
            covered_bars.update(node.bar_locations)
        return len(covered_bars) / self.total_bars

    def variation_diversity(self) -> float:
        """Shannon entropy of transformation types used, normalized.

        Higher values indicate more diverse use of transformations.
        A piece using only transpositions scores lower than one using
        transposition, inversion, retrograde, and augmentation.

        Returns:
            Float in [0.0, 1.0]. 0.0 if only one transformation type.
        """
        if not self.nodes:
            return 0.0

        from collections import Counter

        transform_counts = Counter(node.transformation for node in self.nodes.values())
        total = sum(transform_counts.values())
        if total <= 1:
            return 0.0

        num_types = len(transform_counts)
        if num_types <= 1:
            return 0.0

        entropy = 0.0
        for count in transform_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        max_entropy = math.log2(num_types)
        return entropy / max_entropy if max_entropy > 0 else 0.0
