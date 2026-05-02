"""Producer Subagent — coordinates all others, makes final decisions.

Mirrors .claude/agents/producer.md.
The ONLY Subagent that can override other Subagents' output.
"""

from __future__ import annotations

# Ensure plan generators are registered
import yao.generators.plan.form_planner as _fp  # noqa: F401
from yao.generators.legacy_adapter import _v1_to_v2
from yao.generators.plan.base import PLAN_GENERATORS
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    get_subagent,
    register_subagent,
)


@register_subagent(AgentRole.PRODUCER)
class ProducerSubagent(SubagentBase):
    """Orchestrates all Subagents through the pipeline.

    Responsibility boundary:
    - Owns: Pipeline coordination, conflict resolution, overrides
    - Steps 1-5 executed sequentially, feeding outputs forward
    - ONLY Subagent with ``override_other_subagent()`` method
    """

    role = AgentRole.PRODUCER

    def process(self, context: AgentContext) -> AgentOutput:
        """Execute the full Subagent pipeline.

        Args:
            context: Initial pipeline state with spec, intent, trajectory.

        Returns:
            AgentOutput with all plan components and provenance.
        """
        prov = ProvenanceLog()
        overrides: dict[str, str] = {}
        current_ctx = context

        # Step 1: Form planning (Producer owns this via plan generator)
        spec_v2 = _v1_to_v2(context.spec)
        form_planner = PLAN_GENERATORS["rule_based_form"]()
        form_result = form_planner.generate(spec_v2, context.trajectory, prov)
        form_plan = form_result["form"]

        current_ctx = AgentContext(
            spec=current_ctx.spec,
            intent=current_ctx.intent,
            trajectory=current_ctx.trajectory,
            form_plan=form_plan,
        )

        # Step 2: Harmony
        harmony_agent = get_subagent(AgentRole.HARMONY_THEORIST)
        harmony_out = harmony_agent.process(current_ctx)
        for rec in harmony_out.provenance.records:
            prov.add(rec)
        current_ctx = AgentContext(
            spec=current_ctx.spec,
            intent=current_ctx.intent,
            trajectory=current_ctx.trajectory,
            form_plan=current_ctx.form_plan,
            harmony_plan=harmony_out.harmony_plan,
        )

        # Step 3: Composer (motif + phrase)
        composer_agent = get_subagent(AgentRole.COMPOSER)
        composer_out = composer_agent.process(current_ctx)
        for rec in composer_out.provenance.records:
            prov.add(rec)
        current_ctx = AgentContext(
            spec=current_ctx.spec,
            intent=current_ctx.intent,
            trajectory=current_ctx.trajectory,
            form_plan=current_ctx.form_plan,
            harmony_plan=current_ctx.harmony_plan,
            motif_plan=composer_out.motif_plan,
            phrase_plan=composer_out.phrase_plan,
        )

        # Step 4: Rhythm
        rhythm_agent = get_subagent(AgentRole.RHYTHM_ARCHITECT)
        rhythm_out = rhythm_agent.process(current_ctx)
        for rec in rhythm_out.provenance.records:
            prov.add(rec)
        current_ctx = AgentContext(
            spec=current_ctx.spec,
            intent=current_ctx.intent,
            trajectory=current_ctx.trajectory,
            form_plan=current_ctx.form_plan,
            harmony_plan=current_ctx.harmony_plan,
            motif_plan=current_ctx.motif_plan,
            phrase_plan=current_ctx.phrase_plan,
            drum_pattern=rhythm_out.drum_pattern,
        )

        # Step 5: Orchestration
        orchestrator_agent = get_subagent(AgentRole.ORCHESTRATOR)
        orchestrator_out = orchestrator_agent.process(current_ctx)
        for rec in orchestrator_out.provenance.records:
            prov.add(rec)

        prov.record(
            layer="subagent",
            operation="producer_pipeline_complete",
            parameters={
                "steps_executed": ["form", "harmony", "composer", "rhythm", "orchestration"],
                "overrides": overrides,
            },
            source="ProducerSubagent.process",
            rationale="Producer completed Steps 1-5 pipeline.",
        )

        return AgentOutput(
            provenance=prov,
            form_plan=form_plan,
            harmony_plan=harmony_out.harmony_plan,
            motif_plan=composer_out.motif_plan,
            phrase_plan=composer_out.phrase_plan,
            drum_pattern=rhythm_out.drum_pattern,
            arrangement_plan=orchestrator_out.arrangement_plan,
            overrides=overrides,
        )

    def override_other_subagent(
        self,
        role: AgentRole,
        reason: str,
        provenance: ProvenanceLog,
    ) -> None:
        """Record an override of another Subagent's output.

        This method exists ONLY on ProducerSubagent.

        Args:
            role: The role being overridden.
            reason: Human-readable justification.
            provenance: Log to record the override in.
        """
        provenance.record(
            layer="subagent",
            operation="producer_override",
            parameters={
                "overridden_role": role.value,
                "reason": reason,
            },
            source="ProducerSubagent.override_other_subagent",
            rationale=f"Producer overrode {role.value}: {reason}",
        )
