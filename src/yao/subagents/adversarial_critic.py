"""Adversarial Critic Subagent — finds every weakness, never praises.

Mirrors .claude/agents/adversarial-critic.md.
Wraps the existing 15+ critique rules from verify/critique/.
"""

from __future__ import annotations

from yao.generators.legacy_adapter import _v1_to_v2
from yao.ir.plan.musical_plan import MusicalPlan
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import (
    AgentContext,
    AgentOutput,
    AgentRole,
    SubagentBase,
    register_subagent,
)
from yao.verify.critique import CRITIQUE_RULES
from yao.verify.critique.types import Finding


@register_subagent(AgentRole.ADVERSARIAL_CRITIC)
class AdversarialCriticSubagent(SubagentBase):
    """Runs all critique rules against a MusicalPlan.

    Responsibility boundary:
    - Owns: Findings (structured weakness reports)
    - Does NOT own: generation, correction, approval
    - NEVER praises — only identifies weaknesses
    """

    role = AgentRole.ADVERSARIAL_CRITIC

    def process(self, context: AgentContext) -> AgentOutput:
        """Run all critique rules against the assembled plan.

        Args:
            context: Pipeline state with plan components.

        Returns:
            AgentOutput with findings.
        """
        prov = ProvenanceLog()

        # Assemble a MusicalPlan from context fields if enough data exists
        findings: tuple[Finding, ...] = ()
        if context.form_plan is not None and context.harmony_plan is not None:
            plan = MusicalPlan(
                form=context.form_plan,
                harmony=context.harmony_plan,
                trajectory=context.trajectory,
                intent=context.intent,
                provenance=ProvenanceLog(),
                motif=context.motif_plan,
                phrase=context.phrase_plan,
                arrangement=context.arrangement_plan,
                drums=context.drum_pattern,
            )
            spec_v2 = _v1_to_v2(context.spec)
            raw_findings = CRITIQUE_RULES.run_all(plan, spec_v2)
            findings = tuple(raw_findings)

        prov.record(
            layer="subagent",
            operation="adversarial_critic_complete",
            parameters={
                "findings_count": len(findings),
                "critical": sum(1 for f in findings if f.severity.value == "critical"),
                "major": sum(1 for f in findings if f.severity.value == "major"),
                "minor": sum(1 for f in findings if f.severity.value == "minor"),
            },
            source="AdversarialCriticSubagent.process",
            rationale=f"Adversarial Critic found {len(findings)} issue(s).",
        )

        return AgentOutput(
            provenance=prov,
            findings=findings,
        )
