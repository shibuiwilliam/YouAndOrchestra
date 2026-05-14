"""Streaming event types for the YaO Conductor loop.

UIs subscribe to these events to show real-time progress at the
granularity composers care about: phase transitions, iteration
completions, critique availability, and audio readiness.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class YaoEvent:
    """Base event emitted during a YaO composition workflow."""

    iteration: int = 0
    phase: str = ""
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class PhaseStartedEvent(YaoEvent):
    """Emitted when one of the six cognitive phases begins."""

    intent_summary: str | None = None


@dataclass
class PhaseCompletedEvent(YaoEvent):
    """Emitted when a cognitive phase completes."""


@dataclass
class SubagentStartedEvent(YaoEvent):
    """Emitted when a subagent begins working."""

    subagent_name: str = ""


@dataclass
class IterationCompletedEvent(YaoEvent):
    """Emitted after each Conductor iteration completes."""

    iteration_path: str = ""
    evaluation: dict[str, Any] = field(default_factory=dict)
    pass_status: bool = False


@dataclass
class EvaluationReportEvent(YaoEvent):
    """Emitted when evaluation.json is written."""

    evaluation_json_path: str = ""
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class CritiqueAvailableEvent(YaoEvent):
    """Emitted when critique.md is written."""

    critique_md_path: str = ""
    severity_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class AudioReadyEvent(YaoEvent):
    """Emitted when WAV rendering finishes."""

    wav_path: str = ""
    duration_seconds: float = 0.0


@dataclass
class ProvenanceUpdatedEvent(YaoEvent):
    """Emitted after every provenance append."""

    provenance_path: str = ""
    record_count: int = 0


@dataclass
class ConductorFinishedEvent(YaoEvent):
    """Emitted at the end of a conduct() run."""

    final_iteration_path: str = ""
    total_iterations: int = 0
    status: str = "completed"
