"""Core types for the critique system.

Finding is the structured output of every critique rule. It replaces
free-text critique with machine-actionable data that the Conductor
and Claude Code can process programmatically.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    """Musical role that a critique rule targets."""

    MELODY = "melody"
    BASS = "bass"
    HARMONY = "harmony"
    RHYTHM = "rhythm"
    ARRANGEMENT = "arrangement"
    STRUCTURE = "structure"
    EMOTIONAL = "emotional"
    ACOUSTIC = "acoustic"


class Severity(StrEnum):
    """How serious a finding is."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    SUGGESTION = "suggestion"


@dataclass(frozen=True)
class SongLocation:
    """Identifies a specific location within the composition.

    Attributes:
        section: Section id (e.g., "chorus").
        bars: Bar range as (start, end) tuple, or None for entire section.
        instrument: Instrument name, or None for all.
    """

    section: str | None = None
    bars: tuple[int, int] | None = None
    instrument: str | None = None


@dataclass(frozen=True)
class Finding:
    """A structured critique finding.

    Every critique rule emits Finding objects — never free text.
    Findings are machine-actionable: the Conductor can route them
    to specific generators for remediation.

    Attributes:
        rule_id: Unique identifier (e.g., "harmonic.cliche_progression").
        severity: How serious the issue is.
        role: Which musical role this affects.
        issue: Short description of the problem.
        evidence: Numerical proof supporting the finding.
        location: Where in the piece the issue occurs.
        recommendation: Concrete fix suggestions, keyed by role.
    """

    rule_id: str
    severity: Severity
    role: Role
    issue: str
    evidence: dict[str, Any] = field(default_factory=dict)
    location: SongLocation | None = None
    recommendation: dict[str, str] = field(default_factory=dict)
