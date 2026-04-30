"""MotifPlan — motif and thematic development plan.

Defines seed motifs, their variations, and placement across sections.
A motif is a short melodic-rhythmic idea that recurs and develops
throughout the composition, providing memorability and coherence.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MotifTransform(StrEnum):
    """Transformation applied to a motif to create a variation."""

    IDENTITY = "identity"
    SEQUENCE_UP = "sequence_up"
    SEQUENCE_DOWN = "sequence_down"
    INVERSION = "inversion"
    RETROGRADE = "retrograde"
    AUGMENTATION = "augmentation"
    DIMINUTION = "diminution"
    VARIED_RHYTHM = "varied_rhythm"
    VARIED_INTERVALS = "varied_intervals"


@dataclass(frozen=True)
class MotifSeed:
    """A seed motif — the raw melodic-rhythmic idea.

    Attributes:
        id: Unique identifier for this motif (e.g., "M1", "M2").
        rhythm_shape: Duration pattern in beats (e.g., (1.0, 0.5, 0.5, 1.0)).
        interval_shape: Interval pattern in semitones from first note
            (e.g., (0, 2, 4, 5) for ascending stepwise motion).
        origin_section: Section where this motif first appears.
        character: Brief description (e.g., "lyrical ascending", "rhythmic hook").
    """

    id: str
    rhythm_shape: tuple[float, ...]
    interval_shape: tuple[int, ...]
    origin_section: str
    character: str = ""

    def length_beats(self) -> float:
        """Total duration of the motif in beats."""
        return sum(self.rhythm_shape)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "rhythm_shape": list(self.rhythm_shape),
            "interval_shape": list(self.interval_shape),
            "origin_section": self.origin_section,
            "character": self.character,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MotifSeed:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            rhythm_shape=tuple(data["rhythm_shape"]),
            interval_shape=tuple(data["interval_shape"]),
            origin_section=data["origin_section"],
            character=data.get("character", ""),
        )


@dataclass(frozen=True)
class MotifPlacement:
    """Where and how a motif appears in the composition.

    Attributes:
        motif_id: Reference to a MotifSeed.id.
        section_id: Section where this placement occurs.
        start_beat: Beat position (absolute from piece start).
        transform: Transformation applied to the seed.
        transposition: Semitones to transpose (0 = original pitch level).
        intensity: How much the variation differs from the seed (0.0–1.0).
    """

    motif_id: str
    section_id: str
    start_beat: float
    transform: MotifTransform = MotifTransform.IDENTITY
    transposition: int = 0
    intensity: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "motif_id": self.motif_id,
            "section_id": self.section_id,
            "start_beat": self.start_beat,
            "transform": self.transform.value,
            "transposition": self.transposition,
            "intensity": self.intensity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MotifPlacement:
        """Deserialize from dict."""
        return cls(
            motif_id=data["motif_id"],
            section_id=data["section_id"],
            start_beat=data["start_beat"],
            transform=MotifTransform(data.get("transform", "identity")),
            transposition=data.get("transposition", 0),
            intensity=data.get("intensity", 0.0),
        )


@dataclass(frozen=True)
class MotifPlan:
    """Plan for all motifs and their development across the composition.

    Attributes:
        seeds: The seed motifs (typically 1–3).
        placements: Where each motif appears (ordered by start_beat).
    """

    seeds: list[MotifSeed] = field(default_factory=list)
    placements: list[MotifPlacement] = field(default_factory=list)

    def seed_by_id(self, motif_id: str) -> MotifSeed | None:
        """Find a seed by its id."""
        for seed in self.seeds:
            if seed.id == motif_id:
                return seed
        return None

    def placements_in_section(self, section_id: str) -> list[MotifPlacement]:
        """Return all placements in a given section."""
        return [p for p in self.placements if p.section_id == section_id]

    def recurrence_count(self, motif_id: str) -> int:
        """Count how many times a motif appears across the piece."""
        return sum(1 for p in self.placements if p.motif_id == motif_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "seeds": [s.to_dict() for s in self.seeds],
            "placements": [p.to_dict() for p in self.placements],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MotifPlan:
        """Deserialize from dict."""
        return cls(
            seeds=[MotifSeed.from_dict(s) for s in data.get("seeds", [])],
            placements=[MotifPlacement.from_dict(p) for p in data.get("placements", [])],
        )
