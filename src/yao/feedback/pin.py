"""Pin — localized user feedback attached to a specific musical position.

Pins are immutable user input. Once created, they MUST NOT be modified.
They overlay constraints on regeneration without mutating the spec.

Belongs to Layer 1.5 (Feedback).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal


@dataclass(frozen=True)
class PinLocation:
    """Identifies a specific position within a composition.

    Attributes:
        section: Section name (e.g., "chorus").
        bar: Bar number within the section (1-indexed).
        beat: Beat within the bar (1-indexed). None for entire bar.
        instrument: Instrument name. None for all instruments.
    """

    section: str
    bar: int
    beat: float | None = None
    instrument: str | None = None

    def __post_init__(self) -> None:
        """Validate pin location."""
        if self.bar < 1:
            msg = f"Bar must be >= 1, got {self.bar}"
            raise ValueError(msg)
        if self.beat is not None and self.beat < 1.0:
            msg = f"Beat must be >= 1.0, got {self.beat}"
            raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        result: dict[str, Any] = {
            "section": self.section,
            "bar": self.bar,
        }
        if self.beat is not None:
            result["beat"] = self.beat
        if self.instrument is not None:
            result["instrument"] = self.instrument
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PinLocation:
        """Deserialize from dict."""
        return cls(
            section=data["section"],
            bar=data["bar"],
            beat=data.get("beat"),
            instrument=data.get("instrument"),
        )

    @classmethod
    def from_string(cls, loc_str: str) -> PinLocation:
        """Parse from CLI string format.

        Format: "section:chorus,bar:6,beat:3,instrument:piano"
        Only section and bar are required.

        Args:
            loc_str: Location string in key:value,key:value format.

        Returns:
            Parsed PinLocation.

        Raises:
            ValueError: If parsing fails or required fields are missing.
        """
        parts = {}
        for pair in loc_str.split(","):
            pair = pair.strip()
            if ":" not in pair:
                msg = f"Invalid location pair: '{pair}'. Expected key:value format."
                raise ValueError(msg)
            key, value = pair.split(":", 1)
            parts[key.strip()] = value.strip()

        if "section" not in parts:
            msg = "Location must include 'section'"
            raise ValueError(msg)
        if "bar" not in parts:
            msg = "Location must include 'bar'"
            raise ValueError(msg)

        return cls(
            section=parts["section"],
            bar=int(parts["bar"]),
            beat=float(parts["beat"]) if "beat" in parts else None,
            instrument=parts.get("instrument"),
        )


# Recognized user intents that can be derived from pin notes
PinIntent = Literal[
    "soften_dissonance",
    "increase_intensity",
    "decrease_intensity",
    "add_variation",
    "simplify",
    "change_rhythm",
    "change_harmony",
    "change_melody",
    "too_busy",
    "too_sparse",
    "too_loud",
    "too_soft",
    "unclear",
]


@dataclass(frozen=True)
class Pin:
    """A localized user feedback pin.

    Pins are immutable. Once created via the CLI, they cannot be
    modified. They drive targeted regeneration by overlaying
    constraints on the pinned region.

    Attributes:
        id: Unique pin identifier (e.g., "pin-001").
        location: Where in the piece this pin targets.
        note: User's natural-language comment.
        user_intent: Parsed intent from the note.
        severity: How important this feedback is.
        created_at: When the pin was created (ISO 8601).

    Example:
        >>> pin = Pin(
        ...     id="pin-001",
        ...     location=PinLocation(section="chorus", bar=6, beat=3.0, instrument="piano"),
        ...     note="this dissonance is too harsh",
        ...     user_intent="soften_dissonance",
        ...     severity="medium",
        ... )
    """

    id: str
    location: PinLocation
    note: str
    user_intent: PinIntent = "unclear"
    severity: Literal["low", "medium", "high"] = "medium"
    created_at: str = ""

    def __post_init__(self) -> None:
        """Set created_at if not provided."""
        if not self.created_at:
            # Bypass frozen by using object.__setattr__
            object.__setattr__(self, "created_at", datetime.now(tz=UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "location": self.location.to_dict(),
            "note": self.note,
            "user_intent": self.user_intent,
            "severity": self.severity,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pin:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            location=PinLocation.from_dict(data["location"]),
            note=data["note"],
            user_intent=data.get("user_intent", "unclear"),
            severity=data.get("severity", "medium"),
            created_at=data.get("created_at", ""),
        )

    def affected_bar_range(self, padding: int = 1) -> tuple[int, int]:
        """Return the bar range affected by this pin (with padding).

        Args:
            padding: Number of bars of padding on each side.

        Returns:
            Tuple of (start_bar, end_bar) within the section (1-indexed, inclusive).
        """
        start = max(1, self.location.bar - padding)
        end = self.location.bar + padding
        return (start, end)
