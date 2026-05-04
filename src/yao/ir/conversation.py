"""ConversationPlan IR — inter-instrument dialogue structure.

Defines how instruments interact: call-and-response patterns,
voice focus per section, and reactive fill opportunities.

The Conversation Director Subagent produces a ConversationPlan
that the Note Realizer respects during realization.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ConversationEventType = Literal[
    "call_response",
    "fill_in_response",
    "tutti",
    "solo_break",
    "trade",
]


@dataclass(frozen=True)
class BarRange:
    """A contiguous range of bars.

    Attributes:
        start: Start bar (0-indexed, inclusive).
        end: End bar (exclusive).
    """

    start: int
    end: int

    def __post_init__(self) -> None:
        """Validate bar range."""
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end <= self.start:
            raise ValueError(f"end must be > start, got start={self.start}, end={self.end}")

    @property
    def length(self) -> int:
        """Number of bars in the range."""
        return self.end - self.start

    def contains(self, bar: int) -> bool:
        """Check if a bar is within this range."""
        return self.start <= bar < self.end

    def to_dict(self) -> dict[str, int]:
        """Serialize to dict."""
        return {"start": self.start, "end": self.end}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BarRange:
        """Deserialize from dict."""
        return cls(start=data["start"], end=data["end"])


@dataclass(frozen=True)
class ConversationEvent:
    """A single inter-instrument dialogue event.

    Attributes:
        type: The conversation pattern type.
        initiator: Instrument that starts the dialogue.
        responder: Instrument that responds (None for tutti/solo_break).
        location: Bar range where this event occurs.
        duration_beats: Duration of the event in beats.
    """

    type: ConversationEventType
    initiator: str
    responder: str | None
    location: BarRange
    duration_beats: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "type": self.type,
            "initiator": self.initiator,
            "responder": self.responder,
            "location": self.location.to_dict(),
            "duration_beats": self.duration_beats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversationEvent:
        """Deserialize from dict."""
        return cls(
            type=data["type"],
            initiator=data["initiator"],
            responder=data.get("responder"),
            location=BarRange.from_dict(data["location"]),
            duration_beats=data["duration_beats"],
        )


@dataclass(frozen=True)
class ConversationPlan:
    """Plan for inter-instrument dialogue across the composition.

    Attributes:
        events: Ordered sequence of conversation events.
        primary_voice_per_section: Maps section_id → primary instrument.
        accompaniment_role_per_section: Maps section_id → accompaniment instruments.
    """

    events: tuple[ConversationEvent, ...] = ()
    primary_voice_per_section: dict[str, str] = field(default_factory=dict)
    accompaniment_role_per_section: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def events_in_bar(self, bar: int) -> list[ConversationEvent]:
        """Return all events active at a given bar."""
        return [e for e in self.events if e.location.contains(bar)]

    def primary_voice_for_section(self, section_id: str) -> str | None:
        """Get the primary voice instrument for a section."""
        return self.primary_voice_per_section.get(section_id)

    def accompaniment_for_section(self, section_id: str) -> tuple[str, ...]:
        """Get accompaniment instruments for a section."""
        return self.accompaniment_role_per_section.get(section_id, ())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "events": [e.to_dict() for e in self.events],
            "primary_voice_per_section": dict(self.primary_voice_per_section),
            "accompaniment_role_per_section": {k: list(v) for k, v in self.accompaniment_role_per_section.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversationPlan:
        """Deserialize from dict."""
        events = tuple(ConversationEvent.from_dict(e) for e in data.get("events", []))
        accompaniment = {k: tuple(v) for k, v in data.get("accompaniment_role_per_section", {}).items()}
        return cls(
            events=events,
            primary_voice_per_section=data.get("primary_voice_per_section", {}),
            accompaniment_role_per_section=accompaniment,
        )
