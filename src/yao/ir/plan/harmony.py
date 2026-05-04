"""HarmonyPlan — harmonic structure plan for a composition.

Defines chord events with functional analysis, cadences, and modulations.
This is Step 2 of the 7-step generation pipeline (PROJECT.md §8).

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from yao.ir.tension_arc import TensionArc


class HarmonicFunction(StrEnum):
    """Functional role of a chord in its key context."""

    TONIC = "tonic"
    SUBDOMINANT = "subdominant"
    DOMINANT = "dominant"
    PREDOMINANT = "predominant"
    OTHER = "other"


class CadenceRole(StrEnum):
    """Type of cadence at a phrase/section boundary."""

    HALF = "half"
    AUTHENTIC = "authentic"
    PLAGAL = "plagal"
    DECEPTIVE = "deceptive"


@dataclass(frozen=True)
class ChordEvent:
    """A single chord in the harmonic plan.

    Attributes:
        section_id: Which section this chord belongs to.
        start_beat: Beat position (absolute from piece start).
        duration_beats: Duration in beats.
        roman: Roman numeral notation (e.g., "I", "vi", "V/V", "bVII").
        function: Harmonic function of this chord.
        tension_level: Tension level [0, 1] at this chord.
        cadence_role: Cadence role if this chord is part of a cadence.
    """

    section_id: str
    start_beat: float
    duration_beats: float
    roman: str
    function: HarmonicFunction
    tension_level: float
    cadence_role: CadenceRole | None = None

    def end_beat(self) -> float:
        """Return the exclusive end beat."""
        return self.start_beat + self.duration_beats

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "section_id": self.section_id,
            "start_beat": self.start_beat,
            "duration_beats": self.duration_beats,
            "roman": self.roman,
            "function": self.function.value,
            "tension_level": self.tension_level,
            "cadence_role": self.cadence_role.value if self.cadence_role else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChordEvent:
        """Deserialize from dict."""
        return cls(
            section_id=data["section_id"],
            start_beat=data["start_beat"],
            duration_beats=data["duration_beats"],
            roman=data["roman"],
            function=HarmonicFunction(data["function"]),
            tension_level=data["tension_level"],
            cadence_role=CadenceRole(data["cadence_role"]) if data.get("cadence_role") else None,
        )


@dataclass(frozen=True)
class ModulationEvent:
    """A key change event.

    Attributes:
        at_beat: Beat position where the modulation occurs.
        from_key: Source key (e.g., "C major").
        to_key: Target key (e.g., "G major").
        method: Modulation technique (e.g., "pivot_chord", "direct").
    """

    at_beat: float
    from_key: str
    to_key: str
    method: str = "pivot_chord"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "at_beat": self.at_beat,
            "from_key": self.from_key,
            "to_key": self.to_key,
            "method": self.method,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModulationEvent:
        """Deserialize from dict."""
        return cls(
            at_beat=data["at_beat"],
            from_key=data["from_key"],
            to_key=data["to_key"],
            method=data.get("method", "pivot_chord"),
        )


@dataclass(frozen=True)
class HarmonyPlan:
    """Harmonic structure plan for the entire composition.

    Contains the chord progression with functional analysis, cadence
    assignments per section, modulation events, and tension resolution points.

    Attributes:
        chord_events: Ordered list of chord events.
        cadences: Section id → cadence type mapping.
        modulations: List of modulation events.
        tension_resolution_points: Beat positions where tension resolves.
    """

    chord_events: list[ChordEvent] = field(default_factory=list)
    cadences: dict[str, CadenceRole] = field(default_factory=dict)
    modulations: list[ModulationEvent] = field(default_factory=list)
    tension_resolution_points: list[float] = field(default_factory=list)
    tension_arcs: tuple[TensionArc, ...] = ()

    def chord_at_beat(self, beat: float) -> ChordEvent | None:
        """Find the chord sounding at the given beat.

        Args:
            beat: Beat position (absolute from piece start).

        Returns:
            The ChordEvent active at that beat, or None.
        """
        for chord in self.chord_events:
            if chord.start_beat <= beat < chord.end_beat():
                return chord
        return None

    def chords_in_section(self, section_id: str) -> list[ChordEvent]:
        """Return all chord events belonging to a section.

        Args:
            section_id: Section identifier.

        Returns:
            List of ChordEvents in that section, ordered by start_beat.
        """
        return [c for c in self.chord_events if c.section_id == section_id]

    def section_cadence(self, section_id: str) -> CadenceRole | None:
        """Return the cadence type for a section.

        Args:
            section_id: Section identifier.

        Returns:
            CadenceRole or None if no cadence is assigned.
        """
        return self.cadences.get(section_id)

    def tension_arcs_in_section(self, section_id: str) -> tuple[TensionArc, ...]:
        """Return tension arcs whose location is in the given section.

        Args:
            section_id: Section identifier.

        Returns:
            Tuple of TensionArcs located in that section.
        """
        return tuple(a for a in self.tension_arcs if a.location.section == section_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "chord_events": [c.to_dict() for c in self.chord_events],
            "cadences": {k: v.value for k, v in self.cadences.items()},
            "modulations": [m.to_dict() for m in self.modulations],
            "tension_resolution_points": list(self.tension_resolution_points),
            "tension_arcs": [a.to_dict() for a in self.tension_arcs],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HarmonyPlan:
        """Deserialize from dict."""
        arcs = tuple(TensionArc.from_dict(a) for a in data.get("tension_arcs", []))
        return cls(
            chord_events=[ChordEvent.from_dict(c) for c in data["chord_events"]],
            cadences={k: CadenceRole(v) for k, v in data["cadences"].items()},
            modulations=[ModulationEvent.from_dict(m) for m in data.get("modulations", [])],
            tension_resolution_points=data.get("tension_resolution_points", []),
            tension_arcs=arcs,
        )
