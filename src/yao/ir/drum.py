"""Drum pattern intermediate representation.

Drums are first-class in YaO v1.1 (P1). They have their own IR parallel
to ScoreIR, because drums are conceptually different from pitched notes
(kit pieces vs. pitches, GM Channel 10 mapping, etc.).

Belongs to Layer 3 (IR).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

KitPiece = Literal[
    "kick",
    "snare",
    "rim",
    "closed_hat",
    "open_hat",
    "pedal_hat",
    "clap",
    "tom_low",
    "tom_mid",
    "tom_high",
    "crash",
    "ride",
    "ride_bell",
    "shaker",
    "tambourine",
]

GM_DRUM_MAP: dict[str, int] = {
    "kick": 36,
    "snare": 38,
    "rim": 37,
    "closed_hat": 42,
    "open_hat": 46,
    "pedal_hat": 44,
    "clap": 39,
    "tom_low": 41,
    "tom_mid": 47,
    "tom_high": 50,
    "crash": 49,
    "ride": 51,
    "ride_bell": 53,
    "shaker": 70,
    "tambourine": 54,
}


@dataclass(frozen=True)
class DrumHit:
    """A single drum hit at a specific time.

    Attributes:
        time_beats: Position in beats (0-indexed from pattern start).
        duration_beats: Duration in beats (typically 0.25 for hits).
        kit_piece: Which drum kit piece is struck.
        velocity: MIDI velocity (1-127).
        microtiming_ms: Humanization offset in ms (negative=ahead, positive=behind).
    """

    time_beats: float
    duration_beats: float
    kit_piece: KitPiece
    velocity: int
    microtiming_ms: float = 0.0

    def to_midi_pitch(self) -> int:
        """Return the General MIDI pitch for this kit piece."""
        return GM_DRUM_MAP[self.kit_piece]


@dataclass(frozen=True)
class DrumPattern:
    """A complete drum pattern for a section or the whole piece.

    Attributes:
        id: Pattern identifier (e.g., "pop_8beat").
        genre: Genre this pattern belongs to.
        time_signature: Time signature (e.g., "4/4").
        hits: The drum hits comprising one cycle of the pattern.
        swing: Swing amount (0.0=straight, 0.67=hard swing).
        humanize_ms: Maximum humanization offset in ms.
        fills_at: Section points where fills should occur.
        bars_per_pattern: How many bars one cycle covers.
    """

    id: str
    genre: str
    time_signature: str = "4/4"
    hits: tuple[DrumHit, ...] = ()
    swing: float = 0.0
    humanize_ms: float = 0.0
    fills_at: tuple[str, ...] = ()
    bars_per_pattern: int = 1

    def kit_pieces_used(self) -> set[str]:
        """Return the set of kit pieces used in this pattern."""
        return {h.kit_piece for h in self.hits}
