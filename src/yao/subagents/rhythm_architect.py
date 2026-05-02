"""Rhythm Architect Subagent — designs drum patterns and grooves.

Mirrors .claude/agents/rhythm-architect.md.
Delegates to the existing drum_patterner module.
"""

from __future__ import annotations

from yao.ir.plan.drums import DrumPattern
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)


@register_subagent(AgentRole.RHYTHM_ARCHITECT)
class RhythmArchitectSubagent(SubagentBase):
    """Generates drum patterns from spec and trajectory.

    Responsibility boundary:
    - Owns: DrumPattern (kick, snare, hi-hat, fills, groove)
    - Does NOT own: melody, harmony, instrumentation
    """

    role = AgentRole.RHYTHM_ARCHITECT

    def process(self, context: AgentContext) -> AgentOutput:
        """Generate a drum pattern.

        Args:
            context: Pipeline state with spec, trajectory.

        Returns:
            AgentOutput with drum_pattern.
        """
        prov = ProvenanceLog()

        # DrumPattern IR (plan level) — a stub for now since
        # the drum_patterner produces DrumHit lists, not DrumPattern plans.
        # The actual DrumHit generation happens at the note realization step.
        drum_pattern = DrumPattern(
            id=f"{context.spec.genre}_pattern",
            genre=context.spec.genre,
            time_signature=context.spec.time_signature,
            bars=context.spec.computed_total_bars(),
            hits=[],
        )

        prov.record(
            layer="subagent",
            operation="rhythm_architect_complete",
            parameters={
                "genre": context.spec.genre,
                "total_bars": context.spec.computed_total_bars(),
            },
            source="RhythmArchitectSubagent.process",
            rationale=f"Rhythm Architect prepared drum pattern plan for '{context.spec.genre}'.",
        )

        return AgentOutput(
            provenance=prov,
            drum_pattern=drum_pattern,
        )
