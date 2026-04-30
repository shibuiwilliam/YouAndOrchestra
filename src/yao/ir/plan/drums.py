"""DrumPattern — drum pattern plan for a composition.

Defines drum patterns as first-class plan components with per-piece
control (kick, snare, hat, etc.), microtiming, ghost notes, and fills.
This elevates rhythm from "syncopation ratio" to instrument-level control.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class KitPiece(StrEnum):
    """Individual drum kit pieces."""

    KICK = "kick"
    SNARE = "snare"
    RIM = "rim"
    CLOSED_HAT = "closed_hat"
    OPEN_HAT = "open_hat"
    CLAP = "clap"
    TOM_LOW = "tom_low"
    TOM_MID = "tom_mid"
    TOM_HIGH = "tom_high"
    CRASH = "crash"
    RIDE = "ride"
    SHAKER = "shaker"


@dataclass(frozen=True)
class DrumHit:
    """A single drum hit in a pattern.

    Attributes:
        time: Beat position within the pattern (0-indexed).
        duration: Duration in beats.
        kit_piece: Which kit piece is struck.
        velocity: MIDI velocity (1–127).
        microtiming_ms: Offset from grid in milliseconds
            (negative = ahead, positive = behind). Creates groove feel.
        is_ghost: Whether this is a ghost note (very soft, subtle).
    """

    time: float
    duration: float
    kit_piece: KitPiece
    velocity: int
    microtiming_ms: float = 0.0
    is_ghost: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "time": self.time,
            "duration": self.duration,
            "kit_piece": self.kit_piece.value,
            "velocity": self.velocity,
            "microtiming_ms": self.microtiming_ms,
            "is_ghost": self.is_ghost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DrumHit:
        """Deserialize from dict."""
        return cls(
            time=data["time"],
            duration=data["duration"],
            kit_piece=KitPiece(data["kit_piece"]),
            velocity=data["velocity"],
            microtiming_ms=data.get("microtiming_ms", 0.0),
            is_ghost=data.get("is_ghost", False),
        )


@dataclass(frozen=True)
class FillLocation:
    """Where a drum fill should occur.

    Attributes:
        section_id: Section containing the fill.
        bar_offset: Bar offset from section start (e.g., last bar = section.bars - 1).
        fill_type: Type of fill (e.g., "tom_cascade", "snare_roll", "simple").
    """

    section_id: str
    bar_offset: int
    fill_type: str = "simple"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "section_id": self.section_id,
            "bar_offset": self.bar_offset,
            "fill_type": self.fill_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FillLocation:
        """Deserialize from dict."""
        return cls(
            section_id=data["section_id"],
            bar_offset=data["bar_offset"],
            fill_type=data.get("fill_type", "simple"),
        )


@dataclass(frozen=True)
class DrumPattern:
    """A drum pattern plan for a section or the entire composition.

    Attributes:
        id: Pattern identifier (e.g., "pop_8beat", "waltz_basic").
        genre: Genre this pattern belongs to.
        time_signature: Time signature (e.g., "4/4", "3/4").
        bars: Number of bars in one cycle of the pattern.
        hits: The drum hits comprising the pattern.
        swing: Swing amount (0.0 = straight, 1.0 = full triplet swing).
        humanize: Humanization amount (0.0–1.0, adds timing/velocity variance).
        ghost_notes_density: Ghost note density (0.0–1.0).
        fills: Fill locations within the composition.
    """

    id: str
    genre: str
    time_signature: str = "4/4"
    bars: int = 1
    hits: list[DrumHit] = field(default_factory=list)
    swing: float = 0.0
    humanize: float = 0.0
    ghost_notes_density: float = 0.0
    fills: list[FillLocation] = field(default_factory=list)

    def hits_for_piece(self, piece: KitPiece) -> list[DrumHit]:
        """Return all hits for a specific kit piece."""
        return [h for h in self.hits if h.kit_piece == piece]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "genre": self.genre,
            "time_signature": self.time_signature,
            "bars": self.bars,
            "hits": [h.to_dict() for h in self.hits],
            "swing": self.swing,
            "humanize": self.humanize,
            "ghost_notes_density": self.ghost_notes_density,
            "fills": [f.to_dict() for f in self.fills],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DrumPattern:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            genre=data["genre"],
            time_signature=data.get("time_signature", "4/4"),
            bars=data.get("bars", 1),
            hits=[DrumHit.from_dict(h) for h in data.get("hits", [])],
            swing=data.get("swing", 0.0),
            humanize=data.get("humanize", 0.0),
            ghost_notes_density=data.get("ghost_notes_density", 0.0),
            fills=[FillLocation.from_dict(f) for f in data.get("fills", [])],
        )
