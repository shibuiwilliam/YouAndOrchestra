"""Rhythmic critique rules — analyze rhythm-level issues.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity


class SyncopationLackDetector(CritiqueRule):
    """Detect when a piece has no syncopation despite having energetic sections.

    If any section has target_tension > 0.6 but no off-beat activity,
    the rhythm may feel too square and lifeless.
    """

    rule_id = "rhythm.syncopation_lack"
    role = Role.RHYTHM

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect lack of syncopation in energetic sections."""
        findings: list[Finding] = []
        sections = plan.form.sections

        energetic_sections = [s for s in sections if s.target_tension > 0.6]  # noqa: PLR2004
        if not energetic_sections:
            return findings

        # All energetic sections have identical density — suggests no rhythmic variation
        densities = [s.target_density for s in energetic_sections]
        if len(set(round(d, 2) for d in densities)) <= 1 and all(d < 0.6 for d in densities):  # noqa: PLR2004
            names = [s.id for s in energetic_sections]
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=(
                        f"Energetic sections {names} have low density ({densities[0]:.2f}), "
                        "suggesting insufficient rhythmic activity for their tension level"
                    ),
                    evidence={
                        "sections": names,
                        "densities": densities,
                        "tensions": [s.target_tension for s in energetic_sections],
                    },
                    recommendation={
                        "rhythm": "Increase density in high-tension sections for more rhythmic drive",
                    },
                )
            )

        return findings


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
