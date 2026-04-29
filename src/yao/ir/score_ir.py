"""Score IR — the central intermediate representation for compositions.

ScoreIR is the lingua franca of YaO: generators produce it, renderers consume it,
verifiers evaluate it. All components are frozen dataclasses for immutability.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.ir.note import Note
from yao.ir.timing import bars_to_beats, beats_to_seconds
from yao.types import BPM, Beat, Seconds


@dataclass(frozen=True)
class Part:
    """A collection of notes for a single instrument.

    Attributes:
        instrument: Canonical instrument name.
        notes: Immutable tuple of notes.
    """

    instrument: str
    notes: tuple[Note, ...]


@dataclass(frozen=True)
class Section:
    """A musical section (intro, verse, chorus, etc.).

    Attributes:
        name: Section name (e.g., "intro", "verse").
        start_bar: Starting bar number (0-indexed).
        end_bar: Ending bar number (exclusive).
        parts: Immutable tuple of parts in this section.
    """

    name: str
    start_bar: int
    end_bar: int
    parts: tuple[Part, ...]

    @property
    def bar_count(self) -> int:
        """Number of bars in this section."""
        return self.end_bar - self.start_bar


@dataclass(frozen=True)
class ScoreIR:
    """Complete intermediate representation of a composition.

    This is the primary data structure that flows between YaO layers.
    Generators produce it, renderers consume it, verifiers evaluate it.

    Attributes:
        title: Composition title.
        tempo_bpm: Tempo in beats per minute.
        time_signature: Time signature (e.g., "4/4").
        key: Key signature (e.g., "C major").
        sections: Immutable tuple of sections.
    """

    title: str
    tempo_bpm: BPM
    time_signature: str
    key: str
    sections: tuple[Section, ...]

    def all_notes(self) -> list[Note]:
        """Return all notes across all sections and parts, sorted by start beat."""
        notes: list[Note] = []
        for section in self.sections:
            for part in section.parts:
                notes.extend(part.notes)
        notes.sort(key=lambda n: (n.start_beat, n.pitch))
        return notes

    def part_for_instrument(self, instrument: str) -> list[Note]:
        """Return all notes for a specific instrument across all sections.

        Args:
            instrument: Canonical instrument name.

        Returns:
            Sorted list of notes for the instrument.
        """
        notes: list[Note] = []
        for section in self.sections:
            for part in section.parts:
                if part.instrument == instrument:
                    notes.extend(part.notes)
        notes.sort(key=lambda n: (n.start_beat, n.pitch))
        return notes

    def instruments(self) -> list[str]:
        """Return sorted list of unique instrument names used."""
        instr: set[str] = set()
        for section in self.sections:
            for part in section.parts:
                instr.add(part.instrument)
        return sorted(instr)

    def total_bars(self) -> int:
        """Return the total number of bars."""
        if not self.sections:
            return 0
        return max(s.end_bar for s in self.sections)

    def total_beats(self) -> Beat:
        """Return the total duration in beats."""
        return bars_to_beats(self.total_bars(), self.time_signature)

    def duration_seconds(self) -> Seconds:
        """Return the total duration in seconds."""
        return beats_to_seconds(self.total_beats(), self.tempo_bpm)
