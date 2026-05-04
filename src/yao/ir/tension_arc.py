"""TensionArc — short-range tension–resolution structures.

A TensionArc describes a 2–8 bar tension–resolution pattern at the
plan level (Layer 3.5). Arcs are first-class plan objects that the
Harmony Planner and Note Realizer use to shape local dynamics and
chord choices.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TensionPattern(StrEnum):
    """Shape of a short-range tension arc."""

    LINEAR_RISE = "linear_rise"
    DIP = "dip"
    PLATEAU = "plateau"
    SPIKE = "spike"
    DECEPTIVE = "deceptive"


@dataclass(frozen=True)
class ArcLocation:
    """Where a tension arc lives within the piece.

    Attributes:
        section: Section identifier (must exist in SongFormPlan).
        bar_start: Starting bar within the section (1-indexed).
        bar_end: Ending bar within the section (inclusive, 1-indexed).
    """

    section: str
    bar_start: int
    bar_end: int

    def span(self) -> int:
        """Return the number of bars this arc covers."""
        return self.bar_end - self.bar_start + 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "section": self.section,
            "bar_start": self.bar_start,
            "bar_end": self.bar_end,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArcLocation:
        """Deserialize from dict."""
        return cls(
            section=data["section"],
            bar_start=data["bar_start"],
            bar_end=data["bar_end"],
        )


@dataclass(frozen=True)
class ArcRelease:
    """Where this arc resolves.

    Attributes:
        section: Section identifier for the release point.
        bar: Bar number within the section (1-indexed).
    """

    section: str
    bar: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"section": self.section, "bar": self.bar}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArcRelease:
        """Deserialize from dict."""
        return cls(section=data["section"], bar=data["bar"])


@dataclass(frozen=True)
class TensionArc:
    """A short-range (2–8 bar) tension–resolution structure.

    Decouples local drama from macro-level trajectory curves.
    The HarmonyPlan embeds these as plan-level annotations that
    Note Realizers respect when shaping dynamics and chord choices.

    Attributes:
        id: Unique identifier for this arc (e.g., "approach_chorus").
        location: Where in the piece this arc lives.
        pattern: Shape of the tension curve.
        target_release: Where the arc resolves. None if unresolved.
        intensity: Peak intensity of this arc [0, 1].
        mechanism: Harmonic mechanism (e.g., "secondary_dominant_chain",
            "chromatic_approach", "rhythmic_acceleration").

    Example:
        >>> arc = TensionArc(
        ...     id="approach_chorus",
        ...     location=ArcLocation(section="verse", bar_start=5, bar_end=8),
        ...     pattern=TensionPattern.LINEAR_RISE,
        ...     target_release=ArcRelease(section="chorus", bar=1),
        ...     intensity=0.8,
        ...     mechanism="secondary_dominant_chain",
        ... )
        >>> arc.location.span()
        4
    """

    id: str
    location: ArcLocation
    pattern: TensionPattern
    target_release: ArcRelease | None
    intensity: float
    mechanism: str = ""

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not 0.0 <= self.intensity <= 1.0:
            msg = f"Intensity must be in [0, 1], got {self.intensity}"
            raise ValueError(msg)
        span = self.location.span()
        if span < 2 or span > 8:
            msg = f"TensionArc span must be 2–8 bars, got {span}"
            raise ValueError(msg)

    def is_resolved(self) -> bool:
        """Return True if this arc has a defined release point."""
        return self.target_release is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        result: dict[str, Any] = {
            "id": self.id,
            "location": self.location.to_dict(),
            "pattern": self.pattern.value,
            "target_release": self.target_release.to_dict() if self.target_release else None,
            "intensity": self.intensity,
            "mechanism": self.mechanism,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TensionArc:
        """Deserialize from dict."""
        release = ArcRelease.from_dict(data["target_release"]) if data.get("target_release") else None
        return cls(
            id=data["id"],
            location=ArcLocation.from_dict(data["location"]),
            pattern=TensionPattern(data["pattern"]),
            target_release=release,
            intensity=data["intensity"],
            mechanism=data.get("mechanism", ""),
        )
