"""Hook IR — memorable musical fragments with deployment strategies.

A Hook is a short (2–4 bar), memorable fragment with a prescribed
deployment strategy that controls when and how often it recurs.
Hooks are distinct from Motifs: a Motif is any recurring idea,
while a Hook is specifically designed for memorability and strategic
placement (withhold-then-release, ascending repetition, etc.).

Hook does NOT inherit from or mutate Motif. It references MotifSeed
by id (motif_ref) and adds deployment metadata.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DeploymentStrategy(StrEnum):
    """How a hook is deployed across the composition.

    - rare: appears once or twice, creating a "golden moment"
    - frequent: appears in every major section (pop chorus hook)
    - withhold_then_release: absent from early sections, appears at climax
    - ascending_repetition: each appearance intensifies (louder/higher/fuller)
    """

    RARE = "rare"
    FREQUENT = "frequent"
    WITHHOLD_THEN_RELEASE = "withhold_then_release"
    ASCENDING_REPETITION = "ascending_repetition"


@dataclass(frozen=True)
class BarPosition:
    """A position within the composition identified by section and bar.

    Attributes:
        section_id: Section identifier (e.g., "chorus_1").
        bar: Bar number within the section (0-indexed).
    """

    section_id: str
    bar: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"section_id": self.section_id, "bar": self.bar}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BarPosition:
        """Deserialize from dict."""
        return cls(section_id=data["section_id"], bar=data.get("bar", 0))


@dataclass(frozen=True)
class Hook:
    """A memorable musical fragment with deployment strategy.

    Hooks reference a MotifSeed by id but are not subclasses of Motif.
    They carry deployment metadata that controls strategic placement.

    Attributes:
        id: Unique identifier (e.g., "main_hook", "secondary_hook").
        motif_ref: Reference to a MotifSeed.id in the MotifPlan.
        deployment: Strategy for when/how the hook recurs.
        appearances: Ordered list of positions where the hook should appear.
        variations_allowed: Whether variations of the hook are acceptable.
        maximum_uses: Maximum number of times the hook should appear.
        distinctive_strength: How distinctive/memorable this hook is [0, 1].
    """

    id: str
    motif_ref: str
    deployment: DeploymentStrategy
    appearances: tuple[BarPosition, ...] = ()
    variations_allowed: bool = True
    maximum_uses: int = 4
    distinctive_strength: float = 0.8

    def appearance_count(self) -> int:
        """Return the number of planned appearances."""
        return len(self.appearances)

    def appears_in_section(self, section_id: str) -> bool:
        """Check if the hook appears in a given section."""
        return any(a.section_id == section_id for a in self.appearances)

    def first_appearance_section(self) -> str | None:
        """Return the section_id of the first appearance, or None."""
        if not self.appearances:
            return None
        return self.appearances[0].section_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "id": self.id,
            "motif_ref": self.motif_ref,
            "deployment": self.deployment.value,
            "appearances": [a.to_dict() for a in self.appearances],
            "variations_allowed": self.variations_allowed,
            "maximum_uses": self.maximum_uses,
            "distinctive_strength": self.distinctive_strength,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hook:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            motif_ref=data["motif_ref"],
            deployment=DeploymentStrategy(data["deployment"]),
            appearances=tuple(BarPosition.from_dict(a) for a in data.get("appearances", [])),
            variations_allowed=data.get("variations_allowed", True),
            maximum_uses=data.get("maximum_uses", 4),
            distinctive_strength=data.get("distinctive_strength", 0.8),
        )


@dataclass(frozen=True)
class HookPlan:
    """Plan for all hooks in the composition.

    Extends MotifPlan conceptually but lives as a separate field
    on MusicalPlan (CLAUDE.md: "Hook does NOT mutate Motif").

    Attributes:
        hooks: Ordered list of hooks (typically 1–2 per piece).
    """

    hooks: list[Hook] = field(default_factory=list)

    def hook_by_id(self, hook_id: str) -> Hook | None:
        """Find a hook by its id."""
        for hook in self.hooks:
            if hook.id == hook_id:
                return hook
        return None

    def hooks_in_section(self, section_id: str) -> list[Hook]:
        """Return all hooks that appear in a given section."""
        return [h for h in self.hooks if h.appears_in_section(section_id)]

    def total_appearances(self) -> int:
        """Total number of hook appearances across the composition."""
        return sum(h.appearance_count() for h in self.hooks)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"hooks": [h.to_dict() for h in self.hooks]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HookPlan:
        """Deserialize from dict."""
        return cls(hooks=[Hook.from_dict(h) for h in data.get("hooks", [])])
