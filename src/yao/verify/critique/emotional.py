"""Emotional critique rules — analyze intent/trajectory alignment.

Rules in this module detect divergence between the stated intent
and the actual musical plan, and between trajectory curves and
the plan's tension/density profiles.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity


class IntentDivergenceDetector(CritiqueRule):
    """Detect when the plan diverges from the stated intent.

    If intent keywords suggest "calm" but max tension exceeds 0.7,
    or if intent suggests "energetic" but max density is below 0.4,
    the output likely won't match the user's expectations.
    """

    rule_id = "emotional.intent_divergence"
    role = Role.EMOTIONAL

    # Intent keyword → expected constraints
    _CALM_KEYWORDS = {"calm", "peaceful", "gentle", "relaxing", "ambient", "serene"}
    _ENERGETIC_KEYWORDS = {"energetic", "fast", "upbeat", "driving", "intense", "powerful"}

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect intent/plan divergence."""
        findings: list[Finding] = []

        intent_text = plan.intent.text.lower() if plan.intent.text else ""
        if not intent_text:
            return findings

        max_tension = max((s.target_tension for s in plan.form.sections), default=0.5)
        max_density = max((s.target_density for s in plan.form.sections), default=0.5)

        # Check calm intent vs high tension
        is_calm = any(kw in intent_text for kw in self._CALM_KEYWORDS)
        if is_calm and max_tension > 0.7:  # noqa: PLR2004
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(f"Intent suggests calm mood but max tension is {max_tension:.2f} (>0.7)"),
                    evidence={
                        "intent_keywords": [kw for kw in self._CALM_KEYWORDS if kw in intent_text],
                        "max_tension": max_tension,
                        "threshold": 0.7,
                    },
                    recommendation={
                        "structure": "Lower tension across all sections to match calm intent",
                    },
                )
            )

        # Check energetic intent vs low density
        is_energetic = any(kw in intent_text for kw in self._ENERGETIC_KEYWORDS)
        if is_energetic and max_density < 0.4:  # noqa: PLR2004
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(f"Intent suggests energetic mood but max density is {max_density:.2f} (<0.4)"),
                    evidence={
                        "intent_keywords": [kw for kw in self._ENERGETIC_KEYWORDS if kw in intent_text],
                        "max_density": max_density,
                        "threshold": 0.4,
                    },
                    recommendation={
                        "rhythm": "Increase density in chorus/verse sections for energy",
                    },
                )
            )

        return findings


class TrajectoryViolationDetector(CritiqueRule):
    """Detect when section tension profiles don't follow the trajectory.

    Compares the trajectory's tension curve at each section's midpoint
    with the section's target_tension. Large discrepancies indicate
    the form planner ignored the trajectory.
    """

    rule_id = "emotional.trajectory_violation"
    role = Role.EMOTIONAL

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect trajectory violations."""
        findings: list[Finding] = []

        for section in plan.form.sections:
            midpoint_bar = float(section.start_bar + section.bars / 2)
            trajectory_tension = plan.trajectory.value_at("tension", midpoint_bar)
            section_tension = section.target_tension

            diff = abs(trajectory_tension - section_tension)
            if diff > 0.3:  # noqa: PLR2004
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=(
                            f"Section '{section.id}' target_tension ({section_tension:.2f}) "
                            f"diverges from trajectory ({trajectory_tension:.2f}) at bar "
                            f"{midpoint_bar:.0f} (diff: {diff:.2f})"
                        ),
                        evidence={
                            "section_tension": section_tension,
                            "trajectory_tension": trajectory_tension,
                            "diff": diff,
                            "threshold": 0.3,
                        },
                        recommendation={
                            "structure": (f"Align section '{section.id}' tension with trajectory curve"),
                        },
                    )
                )

        return findings
