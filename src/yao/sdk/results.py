"""Typed result objects returned by YaoAgent methods.

Each result corresponds to one slash command / YaoAgent method.
Front-ends consume these directly without parsing free text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComposeResult:
    """Result of a single-pass composition."""

    iteration_path: str = ""
    midi_path: str = ""
    evaluation: dict[str, Any] = field(default_factory=dict)
    provenance_entries: int = 0


@dataclass
class ConductResult:
    """Result of a full conduct loop."""

    final_iteration_path: str = ""
    midi_path: str = ""
    iterations: int = 0
    pass_rate: float = 0.0
    quality_score: float = 0.0
    adaptations_applied: list[str] = field(default_factory=list)


@dataclass
class CritiqueResult:
    """Result of an adversarial critique."""

    critique_md_path: str = ""
    issues: list[dict[str, Any]] = field(default_factory=list)
    severity_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class RegenerateSectionResult:
    """Result of a section regeneration."""

    new_iteration_path: str = ""
    midi_path: str = ""
    section_regenerated: str = ""


@dataclass
class RenderResult:
    """Result of audio rendering."""

    wav_path: str = ""
    duration_seconds: float = 0.0
    sample_rate: int = 0


@dataclass
class DiffResult:
    """Result of a score diff."""

    summary: str = ""
    added: int = 0
    removed: int = 0
    modified: int = 0


@dataclass
class EvaluateResult:
    """Result of quality evaluation."""

    evaluation_json_path: str = ""
    pass_rate: float = 0.0
    quality_score: float = 0.0
    passed: bool = False
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class ExplainResult:
    """Result of a provenance query."""

    query: str = ""
    chain: list[dict[str, Any]] = field(default_factory=list)
