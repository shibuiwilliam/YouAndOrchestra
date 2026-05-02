"""Memorability critique rules — detect lack of memorable elements.

Rules:
- MotifAbsenceDetector: no recurring motif detected
- HookWeaknessDetector: hook section lacks distinctive rhythm

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity


class MotifAbsenceDetector(CritiqueRule):
    """Detect compositions with no recurring motif."""

    rule_id = "motif_absence"
    role = Role.EMOTIONAL

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check if motif plan has any seeds."""
        if plan.motif is None or len(plan.motif.seeds) == 0:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue="No motif seeds defined — composition may lack memorable themes.",
                )
            ]
        return []


class HookWeaknessDetector(CritiqueRule):
    """Detect weak hook sections."""

    rule_id = "hook_weakness"
    role = Role.EMOTIONAL

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check if chorus/hook sections have adequate presence."""
        hook_sections = [s for s in plan.form.sections if "chorus" in s.id.lower() or "hook" in s.id.lower()]
        if not hook_sections and len(plan.form.sections) >= 3:  # noqa: PLR2004
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue="No chorus/hook section identified in form plan.",
                )
            ]
        return []
