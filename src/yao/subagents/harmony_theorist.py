"""Harmony Theorist Subagent — designs chord progressions and harmonic structure.

Mirrors .claude/agents/harmony-theorist.md.
Uses Roman numeral notation exclusively.
Delegates to the existing rule-based harmony planner.
"""

from __future__ import annotations

# Ensure harmony planner is registered
import yao.generators.plan.harmony_planner as _hp  # noqa: F401
from yao.generators.legacy_adapter import _v1_to_v2
from yao.generators.plan.base import PLAN_GENERATORS
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)


@register_subagent(AgentRole.HARMONY_THEORIST)
class HarmonyTheoristSubagent(SubagentBase):
    """Generates harmony plans from spec and trajectory.

    Responsibility boundary:
    - Owns: HarmonyPlan (chord progressions, cadences)
    - Does NOT own: melody, rhythm, instrumentation
    """

    role = AgentRole.HARMONY_THEORIST

    def process(self, context: AgentContext) -> AgentOutput:
        """Generate a harmony plan.

        Args:
            context: Pipeline state with spec, trajectory.

        Returns:
            AgentOutput with harmony_plan.
        """
        prov = ProvenanceLog()

        spec_v2 = _v1_to_v2(context.spec)
        planner = PLAN_GENERATORS["rule_based_harmony"]()
        result = planner.generate(spec_v2, context.trajectory, prov)
        harmony_plan = result["harmony"]

        prov.record(
            layer="subagent",
            operation="harmony_theorist_complete",
            parameters={
                "chord_count": len(harmony_plan.chord_events),
            },
            source="HarmonyTheoristSubagent.process",
            rationale="Harmony Theorist generated chord progression plan.",
        )

        return AgentOutput(
            provenance=prov,
            harmony_plan=harmony_plan,
        )
