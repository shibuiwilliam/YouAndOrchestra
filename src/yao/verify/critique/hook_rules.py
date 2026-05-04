"""Hook critique rules — detect hook deployment issues.

Rules:
- HookOveruseDetector: hook appears more than maximum_uses
- HookUnderuseDetector: hook is declared but never appears
- HookMisplacementDetector: withhold_then_release hook in intro

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class HookOveruseDetector(CritiqueRule):
    """Detect hooks that appear more times than their maximum_uses allows."""

    rule_id = "hook.overuse"
    role = Role.MELODY

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check hook appearance count against maximum_uses."""
        findings: list[Finding] = []
        if not hasattr(plan, "hook_plan") or plan.hook_plan is None:
            return findings

        for hook in plan.hook_plan.hooks:
            count = hook.appearance_count()
            if count > hook.maximum_uses:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=(
                            f"Hook '{hook.id}' appears {count} times but "
                            f"maximum_uses is {hook.maximum_uses}. "
                            f"Repetition may reduce memorability."
                        ),
                        evidence={
                            "hook_id": hook.id,
                            "appearances": count,
                            "maximum_uses": hook.maximum_uses,
                        },
                        recommendation={
                            "composer": f"Reduce appearances of hook '{hook.id}' or increase maximum_uses.",
                        },
                    )
                )
        return findings


class HookUnderuseDetector(CritiqueRule):
    """Detect hooks that are declared but never appear."""

    rule_id = "hook.underuse"
    role = Role.MELODY

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check that all declared hooks have at least one appearance."""
        findings: list[Finding] = []
        if not hasattr(plan, "hook_plan") or plan.hook_plan is None:
            return findings

        for hook in plan.hook_plan.hooks:
            if hook.appearance_count() == 0:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Hook '{hook.id}' is declared but has no appearances. "
                            f"A hook that never plays cannot create memorability."
                        ),
                        evidence={
                            "hook_id": hook.id,
                            "motif_ref": hook.motif_ref,
                            "deployment": hook.deployment.value,
                        },
                        recommendation={
                            "composer": (
                                f"Add appearance positions for hook '{hook.id}' or remove it from the hook plan."
                            ),
                        },
                    )
                )
        return findings


class HookMisplacementDetector(CritiqueRule):
    """Detect hooks with withhold_then_release that appear too early.

    A withhold_then_release hook should NOT appear in intro or
    first verse — it should be saved for chorus or climax.
    """

    rule_id = "hook.misplacement"
    role = Role.STRUCTURE

    # Sections where withhold_then_release hooks should NOT first appear
    _EARLY_SECTIONS = frozenset(["intro", "verse", "verse_1", "verse_a"])

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check that withhold hooks don't appear in early sections."""
        findings: list[Finding] = []
        if not hasattr(plan, "hook_plan") or plan.hook_plan is None:
            return findings

        for hook in plan.hook_plan.hooks:
            if hook.deployment.value != "withhold_then_release":
                continue

            first_section = hook.first_appearance_section()
            if first_section is None:
                continue

            # Normalize for comparison
            first_lower = first_section.lower()
            if first_lower in self._EARLY_SECTIONS:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Hook '{hook.id}' uses withhold_then_release strategy "
                            f"but first appears in '{first_section}'. "
                            f"This defeats the withholding effect."
                        ),
                        evidence={
                            "hook_id": hook.id,
                            "first_appearance": first_section,
                            "deployment": hook.deployment.value,
                        },
                        location=SongLocation(section=first_section),
                        recommendation={
                            "composer": (f"Move first appearance of hook '{hook.id}' to chorus or climax section."),
                        },
                    )
                )
        return findings
