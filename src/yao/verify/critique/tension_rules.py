"""Tension arc critique rules — detect unresolved arcs.

Flags tension arcs that build up expectation but never resolve,
creating listener frustration rather than productive tension.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class TensionArcUnresolvedDetector(CritiqueRule):
    """Detect tension arcs with no resolution point.

    A tension arc that builds expectation without a target_release
    creates listener frustration unless the pattern is 'deceptive'
    (where the lack of resolution IS the point).
    """

    rule_id = "harmony.tension_arc_unresolved"
    role = Role.HARMONY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect unresolved tension arcs.

        'deceptive' pattern arcs are exempt — their purpose is
        specifically to deny resolution.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects for unresolved arcs.
        """
        findings: list[Finding] = []

        for arc in plan.harmony.tension_arcs:
            if not arc.is_resolved() and arc.pattern.value != "deceptive":
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR if arc.intensity > 0.6 else Severity.MINOR,
                        role=self.role,
                        issue=(
                            f"TensionArc '{arc.id}' ({arc.pattern.value}, "
                            f"intensity={arc.intensity:.2f}) has no target_release. "
                            "Built-up tension without resolution frustrates listeners."
                        ),
                        evidence={
                            "arc_id": arc.id,
                            "pattern": arc.pattern.value,
                            "intensity": arc.intensity,
                            "section": arc.location.section,
                            "bars": [arc.location.bar_start, arc.location.bar_end],
                        },
                        location=SongLocation(
                            section=arc.location.section,
                            bars=(arc.location.bar_start, arc.location.bar_end),
                        ),
                        recommendation={
                            "harmony": (
                                f"Add a target_release for arc '{arc.id}', "
                                "or change pattern to 'deceptive' if denial of resolution is intentional"
                            ),
                        },
                    )
                )

        return findings
