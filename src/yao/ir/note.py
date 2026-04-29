"""Note — the atomic unit of musical information in YaO's IR.

Notes are frozen dataclasses: once created, they cannot be mutated.
This supports provenance tracking (a logged note stays as-is).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.constants.instruments import INSTRUMENT_RANGES, InstrumentRange
from yao.errors import RangeViolationError
from yao.types import Beat, MidiNote, Velocity


@dataclass(frozen=True)
class Note:
    """A single note in the intermediate representation.

    Attributes:
        pitch: MIDI note number (0–127).
        start_beat: Start position in beats from the beginning.
        duration_beats: Duration in beats.
        velocity: MIDI velocity (0–127).
        instrument: Canonical instrument name (must match constants).
    """

    pitch: MidiNote
    start_beat: Beat
    duration_beats: Beat
    velocity: Velocity
    instrument: str

    def end_beat(self) -> Beat:
        """Return the beat position where this note ends."""
        return self.start_beat + self.duration_beats

    def validate_range(self, instrument_range: InstrumentRange | None = None) -> None:
        """Validate that this note is within the instrument's playable range.

        Args:
            instrument_range: Explicit range to check against.
                If None, looks up the instrument in INSTRUMENT_RANGES.

        Raises:
            RangeViolationError: If the note is outside the instrument's range.
        """
        if instrument_range is None:
            instrument_range = INSTRUMENT_RANGES.get(self.instrument)
        if instrument_range is None:
            return  # Unknown instrument — cannot validate range
        if not instrument_range.midi_low <= self.pitch <= instrument_range.midi_high:
            raise RangeViolationError(
                instrument=self.instrument,
                note=self.pitch,
                valid_low=instrument_range.midi_low,
                valid_high=instrument_range.midi_high,
            )
