"""ArrangementPlan — arrangement and orchestration plan.

Defines per-instrument roles, active sections, register assignments,
and articulation choices. The arrangement plan determines *who plays what*
and *when*, without specifying the exact notes (that's the realizer's job).

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class InstrumentRole(StrEnum):
    """Musical role an instrument plays in a section."""

    MELODY = "melody"
    COUNTER_MELODY = "counter_melody"
    HARMONY = "harmony"
    BASS = "bass"
    PAD = "pad"
    RHYTHM = "rhythm"
    OSTINATO = "ostinato"
    SILENT = "silent"


@dataclass(frozen=True)
class InstrumentAssignment:
    """Assignment of an instrument to a section with role and register.

    Attributes:
        instrument: Instrument name (e.g., "piano", "violin").
        section_id: Section this assignment applies to.
        role: Musical role in this section.
        register_low: Lowest MIDI note allowed.
        register_high: Highest MIDI note allowed.
        articulation: Articulation style (e.g., "legato", "staccato").
        density_factor: Relative note density (0.0–1.0). Lower = sparser.
    """

    instrument: str
    section_id: str
    role: InstrumentRole
    register_low: int = 0
    register_high: int = 127
    articulation: str = "normal"
    density_factor: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "instrument": self.instrument,
            "section_id": self.section_id,
            "role": self.role.value,
            "register_low": self.register_low,
            "register_high": self.register_high,
            "articulation": self.articulation,
            "density_factor": self.density_factor,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InstrumentAssignment:
        """Deserialize from dict."""
        return cls(
            instrument=data["instrument"],
            section_id=data["section_id"],
            role=InstrumentRole(data["role"]),
            register_low=data.get("register_low", 0),
            register_high=data.get("register_high", 127),
            articulation=data.get("articulation", "normal"),
            density_factor=data.get("density_factor", 1.0),
        )


@dataclass(frozen=True)
class ArrangementPlan:
    """Orchestration and arrangement plan for the composition.

    Attributes:
        assignments: Per-instrument, per-section role assignments.
        layer_count_by_section: Target number of active instrument layers per section.
    """

    assignments: list[InstrumentAssignment] = field(default_factory=list)
    layer_count_by_section: dict[str, int] = field(default_factory=dict)

    def assignments_for_section(self, section_id: str) -> list[InstrumentAssignment]:
        """Return all instrument assignments for a section."""
        return [a for a in self.assignments if a.section_id == section_id]

    def assignments_for_instrument(self, instrument: str) -> list[InstrumentAssignment]:
        """Return all section assignments for an instrument."""
        return [a for a in self.assignments if a.instrument == instrument]

    def melody_instrument(self, section_id: str) -> str | None:
        """Find the melody instrument for a section."""
        for a in self.assignments:
            if a.section_id == section_id and a.role == InstrumentRole.MELODY:
                return a.instrument
        return None

    def active_instruments(self, section_id: str) -> list[str]:
        """Return instruments active (non-silent) in a section."""
        return [
            a.instrument for a in self.assignments if a.section_id == section_id and a.role != InstrumentRole.SILENT
        ]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "assignments": [a.to_dict() for a in self.assignments],
            "layer_count_by_section": dict(self.layer_count_by_section),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArrangementPlan:
        """Deserialize from dict."""
        return cls(
            assignments=[InstrumentAssignment.from_dict(a) for a in data.get("assignments", [])],
            layer_count_by_section=data.get("layer_count_by_section", {}),
        )
