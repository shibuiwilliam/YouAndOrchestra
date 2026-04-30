"""SongFormPlan — structural plan for a composition's form.

Defines the section sequence, their roles, and structural properties.
This is Step 1 of the 7-step generation pipeline (PROJECT.md §8).

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class SectionPlan:
    """Plan for a single section of the composition.

    Attributes:
        id: Section identifier (e.g., "intro", "verse_a", "chorus").
        start_bar: Bar number where this section begins (0-indexed).
        bars: Number of bars in this section.
        role: Structural role of this section.
        target_density: Target note density [0, 1].
        target_tension: Target tension level [0, 1].
        is_climax: Whether this section is the piece's climax.
    """

    id: str
    start_bar: int
    bars: int
    role: Literal[
        "intro",
        "verse",
        "pre_chorus",
        "chorus",
        "bridge",
        "solo",
        "interlude",
        "breakdown",
        "build",
        "drop",
        "outro",
        "coda",
    ]
    target_density: float
    target_tension: float
    is_climax: bool = False

    def end_bar(self) -> int:
        """Return the exclusive end bar (start_bar + bars)."""
        return self.start_bar + self.bars

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "start_bar": self.start_bar,
            "bars": self.bars,
            "role": self.role,
            "target_density": self.target_density,
            "target_tension": self.target_tension,
            "is_climax": self.is_climax,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SectionPlan:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            start_bar=data["start_bar"],
            bars=data["bars"],
            role=data["role"],
            target_density=data["target_density"],
            target_tension=data["target_tension"],
            is_climax=data.get("is_climax", False),
        )


@dataclass(frozen=True)
class SongFormPlan:
    """Structural plan for the entire composition.

    Contains the ordered sequence of sections and identifies the climax.
    Trajectory curves are referenced from MusicalPlan, not duplicated here.

    Attributes:
        sections: Ordered list of section plans.
        climax_section_id: The id of the climax section.
    """

    sections: list[SectionPlan] = field(default_factory=list)
    climax_section_id: str = ""

    def total_bars(self) -> int:
        """Return the total number of bars in the form."""
        return sum(s.bars for s in self.sections)

    def section_at_bar(self, bar: int) -> SectionPlan | None:
        """Find the section that contains the given bar.

        Args:
            bar: Bar number (0-indexed).

        Returns:
            The SectionPlan containing that bar, or None if out of range.
        """
        for section in self.sections:
            if section.start_bar <= bar < section.end_bar():
                return section
        return None

    def section_by_id(self, section_id: str) -> SectionPlan | None:
        """Find a section by its id.

        Args:
            section_id: Section identifier.

        Returns:
            The matching SectionPlan, or None.
        """
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def section_ids(self) -> list[str]:
        """Return ordered list of section ids."""
        return [s.id for s in self.sections]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "sections": [s.to_dict() for s in self.sections],
            "climax_section_id": self.climax_section_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SongFormPlan:
        """Deserialize from dict."""
        sections = [SectionPlan.from_dict(s) for s in data["sections"]]
        return cls(
            sections=sections,
            climax_section_id=data["climax_section_id"],
        )
