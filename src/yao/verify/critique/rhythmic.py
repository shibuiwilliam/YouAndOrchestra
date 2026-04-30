"""Rhythmic critique rules — analyze rhythm-level issues.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity


class RhythmicMonotonyDetector(CritiqueRule):
    """Detect when all sections have identical density targets.

    If every section has the same target_density, the rhythmic texture
    will feel static throughout the piece.
    """

    rule_id = "rhythm.monotony"
    role = Role.RHYTHM

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect rhythmic monotony across sections."""
        findings: list[Finding] = []
        sections = plan.form.sections
        if len(sections) < 3:  # noqa: PLR2004
            return findings

        densities = [s.target_density for s in sections]
        density_range = max(densities) - min(densities)

        if density_range < 0.1:  # noqa: PLR2004
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"All {len(sections)} sections have nearly identical density "
                        f"(range: {density_range:.2f}, threshold: 0.1)"
                    ),
                    evidence={
                        "densities": densities,
                        "range": density_range,
                        "threshold": 0.1,
                    },
                    recommendation={
                        "rhythm": ("Vary density across sections: sparse intro/outro, dense chorus, moderate verse"),
                    },
                )
            )

        return findings
