"""Subagent base classes and shared contracts.

Defines the universal interface all Subagents implement:
- ``SubagentBase``: abstract base with ``process()``
- ``AgentRole``: enum of the 7 orchestra members
- ``AgentContext``: frozen input bundle (incrementally populated)
- ``AgentOutput``: frozen output bundle (each Subagent fills its own fields)
- ``@register_subagent``: decorator for the Subagent registry
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from yao.ir.plan.arrangement import ArrangementPlan
from yao.ir.plan.drums import DrumPattern
from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.motif import MotifPlan
from yao.ir.plan.phrase import PhrasePlan
from yao.ir.plan.song_form import SongFormPlan
from yao.ir.score_ir import ScoreIR
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.intent import IntentSpec
from yao.schema.production import ProductionManifest
from yao.verify.critique.types import Finding

# ---------------------------------------------------------------------------
# AgentRole
# ---------------------------------------------------------------------------


class AgentRole(Enum):
    """The 7 orchestra members."""

    COMPOSER = "composer"
    HARMONY_THEORIST = "harmony_theorist"
    RHYTHM_ARCHITECT = "rhythm_architect"
    ORCHESTRATOR = "orchestrator"
    ADVERSARIAL_CRITIC = "adversarial_critic"
    MIX_ENGINEER = "mix_engineer"
    PRODUCER = "producer"


# ---------------------------------------------------------------------------
# AgentContext — universal frozen input
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentContext:
    """Universal input bundle for all Subagents.

    Each Subagent reads what it needs and ignores the rest.
    The Producer incrementally builds context by feeding one
    Subagent's output into the next Subagent's context.

    Attributes:
        spec: Composition specification (always present).
        intent: Intent specification (always present).
        trajectory: Multi-dimensional trajectory (always present).
        form_plan: After Step 1 (Producer).
        harmony_plan: After Step 2 (Harmony Theorist).
        motif_plan: After Step 3 (Composer).
        phrase_plan: After Step 3 (Composer).
        drum_pattern: After Step 4 (Rhythm Architect).
        arrangement_plan: After Step 5 (Orchestrator).
        score: After Step 6 (Note Realizer).
        findings: From Adversarial Critic.
    """

    spec: CompositionSpec
    intent: IntentSpec
    trajectory: MultiDimensionalTrajectory

    form_plan: SongFormPlan | None = None
    harmony_plan: HarmonyPlan | None = None
    motif_plan: MotifPlan | None = None
    phrase_plan: PhrasePlan | None = None
    drum_pattern: DrumPattern | None = None
    arrangement_plan: ArrangementPlan | None = None
    score: ScoreIR | None = None
    findings: tuple[Finding, ...] = ()


# ---------------------------------------------------------------------------
# AgentOutput — universal frozen output
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentOutput:
    """Universal output bundle from a Subagent.

    Each Subagent populates only the fields it owns.
    ``provenance`` is always required (Principle 2).

    Attributes:
        provenance: Append-only decision log (always present).
        form_plan: Produced by Producer (Step 1).
        harmony_plan: Produced by Harmony Theorist.
        motif_plan: Produced by Composer.
        phrase_plan: Produced by Composer.
        drum_pattern: Produced by Rhythm Architect.
        arrangement_plan: Produced by Orchestrator.
        score: Produced by Note Realizer (not a Subagent, but carried).
        findings: Produced by Adversarial Critic.
        production_manifest: Produced by Mix Engineer.
        overrides: Producer-only: records of overridden Subagent outputs.
        escalations: Producer-only: issues escalated to the human.
    """

    provenance: ProvenanceLog

    form_plan: SongFormPlan | None = None
    harmony_plan: HarmonyPlan | None = None
    motif_plan: MotifPlan | None = None
    phrase_plan: PhrasePlan | None = None
    drum_pattern: DrumPattern | None = None
    arrangement_plan: ArrangementPlan | None = None
    score: ScoreIR | None = None
    findings: tuple[Finding, ...] = ()
    production_manifest: ProductionManifest | None = None

    overrides: dict[str, str] = field(default_factory=dict)
    escalations: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# SubagentBase — abstract base
# ---------------------------------------------------------------------------


class SubagentBase(ABC):
    """Abstract base class for all Subagents.

    All Subagents declare their ``role`` and implement ``process()``.
    The contract: ``process()`` receives an ``AgentContext`` and returns
    an ``AgentOutput`` with ``provenance`` always populated.
    """

    role: AgentRole

    @abstractmethod
    def process(self, context: AgentContext) -> AgentOutput:
        """Execute this Subagent's responsibility.

        Args:
            context: The current pipeline state.

        Returns:
            AgentOutput with this Subagent's contribution and provenance.
        """
        ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_SUBAGENT_REGISTRY: dict[AgentRole, type[SubagentBase]] = {}


def register_subagent(role: AgentRole) -> Any:
    """Decorator to register a Subagent class by role.

    Args:
        role: The AgentRole this class implements.

    Returns:
        Decorator that registers the class.

    Example:
        @register_subagent(AgentRole.COMPOSER)
        class ComposerSubagent(SubagentBase): ...
    """

    def decorator(cls: type[SubagentBase]) -> type[SubagentBase]:
        _SUBAGENT_REGISTRY[role] = cls
        return cls

    return decorator


def get_subagent(role: AgentRole) -> SubagentBase:
    """Instantiate a Subagent by role.

    Args:
        role: The AgentRole to look up.

    Returns:
        A new Subagent instance.

    Raises:
        KeyError: If no Subagent is registered for the role.
    """
    cls = _SUBAGENT_REGISTRY.get(role)
    if cls is None:
        available = [r.value for r in _SUBAGENT_REGISTRY]
        raise KeyError(f"No subagent registered for {role}. Available: {available}")
    return cls()


def registered_subagents() -> dict[AgentRole, type[SubagentBase]]:
    """Return the current registry (for testing)."""
    return dict(_SUBAGENT_REGISTRY)
