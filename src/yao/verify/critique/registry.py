"""Critique rule registry.

All critique rules must be registered here. The registry provides
iteration, filtering by role, and execution of all rules.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role


class CritiqueRegistry:
    """Registry of critique rules.

    Rules are registered with register() and executed with run_all().
    """

    def __init__(self) -> None:
        self._rules: list[CritiqueRule] = []

    def register(self, rule: CritiqueRule) -> None:
        """Register a critique rule.

        Args:
            rule: The rule to register.
        """
        self._rules.append(rule)

    def all_rules(self) -> list[CritiqueRule]:
        """Return all registered rules."""
        return list(self._rules)

    def rules_by_role(self, role: Role) -> list[CritiqueRule]:
        """Return rules filtered by role.

        Args:
            role: The role to filter by.

        Returns:
            Rules targeting that role.
        """
        return [r for r in self._rules if r.role == role]

    def run_all(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Run all registered rules against a plan.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            All findings from all rules, concatenated.
        """
        findings: list[Finding] = []
        for rule in self._rules:
            findings.extend(rule.detect(plan, spec))
        return findings

    def __len__(self) -> int:
        return len(self._rules)


# Global registry instance — rules register themselves here
CRITIQUE_RULES = CritiqueRegistry()
