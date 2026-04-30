"""PhrasePlan — phrase structure and contour plan.

Defines how melodic phrases are structured within sections,
including antecedent-consequent relationships, cadence targets,
and contour shapes. Phrases give melodies their conversational
quality — the sense of "question and answer."

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PhraseRole(StrEnum):
    """Structural role of a phrase within its section."""

    ANTECEDENT = "antecedent"
    CONSEQUENT = "consequent"
    STAND_ALONE = "stand_alone"
    CONTINUATION = "continuation"


class PhraseContour(StrEnum):
    """Overall melodic contour shape for a phrase."""

    RISE = "rise"
    FALL = "fall"
    ARCH = "arch"
    INVERTED_ARCH = "inverted_arch"
    WAVE = "wave"
    FLAT = "flat"


class PhraseCadence(StrEnum):
    """Target cadence type for the phrase ending."""

    HALF = "half"
    AUTHENTIC = "authentic"
    PLAGAL = "plagal"
    DECEPTIVE = "deceptive"
    NONE = "none"


@dataclass(frozen=True)
class Phrase:
    """A single phrase within a section.

    Attributes:
        id: Unique phrase identifier.
        section_id: Section this phrase belongs to.
        start_beat: Absolute beat position where phrase begins.
        length_beats: Duration of the phrase in beats.
        role: Structural role (antecedent, consequent, etc.).
        contour: Melodic contour shape.
        cadence: Target cadence at phrase end.
        peak_position: Where the melodic peak occurs (0.0–1.0 through phrase).
    """

    id: str
    section_id: str
    start_beat: float
    length_beats: float
    role: PhraseRole = PhraseRole.STAND_ALONE
    contour: PhraseContour = PhraseContour.ARCH
    cadence: PhraseCadence = PhraseCadence.NONE
    peak_position: float = 0.6

    def end_beat(self) -> float:
        """Return the exclusive end beat."""
        return self.start_beat + self.length_beats

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "section_id": self.section_id,
            "start_beat": self.start_beat,
            "length_beats": self.length_beats,
            "role": self.role.value,
            "contour": self.contour.value,
            "cadence": self.cadence.value,
            "peak_position": self.peak_position,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Phrase:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            section_id=data["section_id"],
            start_beat=data["start_beat"],
            length_beats=data["length_beats"],
            role=PhraseRole(data.get("role", "stand_alone")),
            contour=PhraseContour(data.get("contour", "arch")),
            cadence=PhraseCadence(data.get("cadence", "none")),
            peak_position=data.get("peak_position", 0.6),
        )


@dataclass(frozen=True)
class PhrasePlan:
    """Plan for phrase structure across the entire composition.

    Attributes:
        phrases: Ordered list of phrases (by start_beat).
        bars_per_phrase: Default phrase length in bars (typically 4).
        pattern: High-level phrase grouping pattern (e.g., "AABA", "ABAC").
    """

    phrases: list[Phrase] = field(default_factory=list)
    bars_per_phrase: float = 4.0
    pattern: str = ""

    def phrases_in_section(self, section_id: str) -> list[Phrase]:
        """Return all phrases in a given section."""
        return [p for p in self.phrases if p.section_id == section_id]

    def phrase_at_beat(self, beat: float) -> Phrase | None:
        """Find the phrase containing the given beat."""
        for phrase in self.phrases:
            if phrase.start_beat <= beat < phrase.end_beat():
                return phrase
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "phrases": [p.to_dict() for p in self.phrases],
            "bars_per_phrase": self.bars_per_phrase,
            "pattern": self.pattern,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhrasePlan:
        """Deserialize from dict."""
        return cls(
            phrases=[Phrase.from_dict(p) for p in data.get("phrases", [])],
            bars_per_phrase=data.get("bars_per_phrase", 4.0),
            pattern=data.get("pattern", ""),
        )
