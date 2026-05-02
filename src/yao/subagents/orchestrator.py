"""Orchestrator Subagent — assigns instruments, designs voicings, manages frequency space.

Mirrors .claude/agents/orchestrator.md.
Owns instrument-to-role mapping and arrangement decisions.
"""

from __future__ import annotations

from yao.ir.plan.arrangement import ArrangementPlan, InstrumentAssignment, InstrumentRole
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)


@register_subagent(AgentRole.ORCHESTRATOR)
class OrchestratorSubagent(SubagentBase):
    """Generates arrangement plans from spec and all preceding plans.

    Responsibility boundary:
    - Owns: ArrangementPlan (instrument roles, voicings, register assignments)
    - Does NOT own: melody content, harmony content, critique
    """

    role = AgentRole.ORCHESTRATOR

    def process(self, context: AgentContext) -> AgentOutput:
        """Generate an arrangement plan.

        Args:
            context: Pipeline state with spec and preceding plans.

        Returns:
            AgentOutput with arrangement_plan.
        """
        prov = ProvenanceLog()

        valid_roles = {r.value for r in InstrumentRole}
        assignments: list[InstrumentAssignment] = []
        for instr in context.spec.instruments:
            for section in context.spec.sections:
                role_enum = InstrumentRole(instr.role) if instr.role in valid_roles else InstrumentRole.HARMONY
                assignments.append(
                    InstrumentAssignment(
                        instrument=instr.name,
                        section_id=section.name,
                        role=role_enum,
                    )
                )

        arrangement_plan = ArrangementPlan(
            assignments=assignments,
            layer_count_by_section={s.name: len(context.spec.instruments) for s in context.spec.sections},
        )

        prov.record(
            layer="subagent",
            operation="orchestrator_complete",
            parameters={
                "instrument_count": len(assignments),
                "roles": [(a.instrument, a.role.value) for a in assignments],
            },
            source="OrchestratorSubagent.process",
            rationale="Orchestrator assigned instruments to roles based on spec.",
        )

        return AgentOutput(
            provenance=prov,
            arrangement_plan=arrangement_plan,
        )
