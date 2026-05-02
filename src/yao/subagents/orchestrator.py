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

_ROLE_REGISTER_DEFAULTS: dict[InstrumentRole, tuple[int, int]] = {
    InstrumentRole.BASS: (28, 55),
    InstrumentRole.HARMONY: (48, 72),
    InstrumentRole.PAD: (48, 72),
    InstrumentRole.RHYTHM: (36, 84),
    InstrumentRole.OSTINATO: (48, 72),
    InstrumentRole.MELODY: (60, 84),
    InstrumentRole.COUNTER_MELODY: (55, 79),
    InstrumentRole.SILENT: (0, 127),
}


@register_subagent(AgentRole.ORCHESTRATOR)
class OrchestratorSubagent(SubagentBase):
    """Generates arrangement plans with register separation and role assignment.

    Responsibility boundary:
    - Owns: ArrangementPlan (instrument roles, voicings, register assignments)
    - Does NOT own: melody content, harmony content, critique

    Wave 3.2 enhancement: assigns register ranges per role to ensure
    ensemble separation and avoid frequency collision.
    """

    role = AgentRole.ORCHESTRATOR

    def process(self, context: AgentContext) -> AgentOutput:
        """Generate an arrangement plan with register-aware assignments.

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

                # Assign register based on role (Wave 3.2)
                reg_low, reg_high = self._register_for_role(role_enum, instr.name)

                assignments.append(
                    InstrumentAssignment(
                        instrument=instr.name,
                        section_id=section.name,
                        role=role_enum,
                        register_low=reg_low,
                        register_high=reg_high,
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
                "roles": [(a.instrument, a.role.value, a.register_low, a.register_high) for a in assignments],
            },
            source="OrchestratorSubagent.process",
            rationale="Orchestrator assigned instruments to roles with register separation (Wave 3.2).",
        )

        return AgentOutput(
            provenance=prov,
            arrangement_plan=arrangement_plan,
        )

    def _register_for_role(self, role: InstrumentRole, instrument: str) -> tuple[int, int]:
        """Determine register bounds for a role, respecting instrument range."""
        from yao.constants.instruments import INSTRUMENT_RANGES

        role_low, role_high = _ROLE_REGISTER_DEFAULTS.get(role, (0, 127))

        # Constrain to instrument's physical range
        instr_range = INSTRUMENT_RANGES.get(instrument)
        if instr_range:
            role_low = max(role_low, instr_range.midi_low)
            role_high = min(role_high, instr_range.midi_high)

        return role_low, role_high
