"""Subagent message protocol for inter-agent communication.

Every subagent invocation produces a SubagentMessage that is recorded
in Provenance verbatim. See CLAUDE.md §10.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from yao.conductor.protocol import Phase


@dataclass(frozen=True)
class Decision:
    """A single decision made by a subagent.

    Attributes:
        domain: The decision domain (e.g., "harmony", "rhythm", "texture").
        description: What was decided.
        rationale: Why this choice was made.
        confidence: Confidence level in [0.0, 1.0].
        alternatives_rejected: Other options that were considered but not chosen.
    """

    domain: str
    description: str
    rationale: str
    confidence: float
    alternatives_rejected: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Question:
    """A question from one subagent to another.

    Attributes:
        target_agent: Which subagent this question is directed to.
        content: The question text.
        context: Additional context for the question.
    """

    target_agent: str
    content: str
    context: str = ""


@dataclass(frozen=True)
class SubagentMessage:
    """Standard message format for all subagent communications.

    Every subagent invocation must produce one of these. They are
    recorded in Provenance verbatim (CLAUDE.md §10.2).

    Attributes:
        agent: The subagent identifier (e.g., "harmony_theorist").
        phase: Which cognitive phase this message belongs to.
        input_hash: Hash of the input data for reproducibility.
        decisions: List of decisions made during this invocation.
        questions_to_other_agents: Questions directed to other subagents.
        flags: Warning or status flags (e.g., "low_confidence", "needs_review").
        artifacts: Paths to any artifacts produced.
    """

    agent: str
    phase: Phase
    input_hash: str
    decisions: list[Decision] = field(default_factory=list)
    questions_to_other_agents: list[Question] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    artifacts: list[Path] = field(default_factory=list)
