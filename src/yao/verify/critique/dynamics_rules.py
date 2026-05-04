"""Dynamics critique rules — detect flat phrase dynamics.

Rules:
- FlatPhraseDynamicsDetector: section has no dynamics_shape and no accents

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class FlatPhraseDynamicsDetector(CritiqueRule):
    """Detect sections with no dynamics shaping.

    A section without dynamics_shape and without accents will have
    monotone velocity throughout, making it feel mechanical and flat.
    Only fires for sections longer than 2 bars (short sections may
    legitimately be flat).
    """

    rule_id = "dynamics.flat_phrase"
    role = Role.ARRANGEMENT

    _MIN_BARS_TO_CHECK = 3

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check for sections without any dynamics shaping."""
        findings: list[Finding] = []

        if not hasattr(spec, "form") or spec.form is None:
            return findings

        for section in spec.form.sections:
            # Skip short sections
            if section.bars < self._MIN_BARS_TO_CHECK:
                continue

            # Check if section has dynamics_shape
            has_shape = section.dynamics_shape is not None and section.dynamics_shape.shape != "steady"
            has_accents = section.dynamics_shape is not None and len(section.dynamics_shape.accents) > 0

            if not has_shape and not has_accents:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=(
                            f"Section '{section.id}' ({section.bars} bars) has no "
                            f"dynamics_shape or accents. Velocity will be flat throughout."
                        ),
                        evidence={
                            "section_id": section.id,
                            "bars": section.bars,
                            "has_dynamics_shape": has_shape,
                            "has_accents": has_accents,
                        },
                        location=SongLocation(section=section.id),
                        recommendation={
                            "composer": (
                                f"Add dynamics_shape (crescendo, arch, hairpin) to "
                                f"section '{section.id}' for more expressive phrasing."
                            ),
                        },
                    )
                )

        return findings
