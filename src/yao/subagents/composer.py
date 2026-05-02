"""Composer Subagent — generates motifs, phrases, and thematic material.

Mirrors .claude/agents/composer.md.
Does NOT choose instruments (Orchestrator's job).
Does NOT evaluate quality (Critic's job).

In Phase α, delegates to the legacy adapter's plan building since
dedicated motif/phrase generators are not yet implemented.
"""

from __future__ import annotations

from yao.ir.plan.motif import MotifPlan
from yao.ir.plan.phrase import PhrasePlan
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)


@register_subagent(AgentRole.COMPOSER)
class ComposerSubagent(SubagentBase):
    """Generates motif and phrase plans from spec, intent, and trajectory.

    Responsibility boundary:
    - Owns: MotifPlan, PhrasePlan
    - Does NOT own: instruments, voicings, evaluation
    """

    role = AgentRole.COMPOSER

    def process(self, context: AgentContext) -> AgentOutput:
        """Generate motif and phrase plans.

        Args:
            context: Pipeline state with spec, intent, trajectory.

        Returns:
            AgentOutput with motif_plan and phrase_plan.
        """
        prov = ProvenanceLog()

        # Phase α: MotifPlan and PhrasePlan are stubs from the plan builder.
        # When dedicated motif/phrase generators land, this will call them directly.
        motif_plan = MotifPlan(seeds=[], placements=[])
        phrase_plan = PhrasePlan(phrases=[], bars_per_phrase=4.0, pattern="")

        prov.record(
            layer="subagent",
            operation="composer_complete",
            parameters={
                "motif_count": len(motif_plan.seeds),
                "phrase_count": len(phrase_plan.phrases),
            },
            source="ComposerSubagent.process",
            rationale="Composer generated motif and phrase plans (Phase α stubs).",
        )

        return AgentOutput(
            provenance=prov,
            motif_plan=motif_plan,
            phrase_plan=phrase_plan,
        )
