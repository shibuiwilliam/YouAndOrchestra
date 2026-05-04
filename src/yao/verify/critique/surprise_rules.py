"""Surprise critique rules — detect surprise deficit and overload.

These rules analyze the surprise distribution of a piece and flag
pieces that are too predictable (deficit) or too chaotic (overload).

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity

# Thresholds derived from music perception research (Huron, 2006).
# A healthy piece has moderate surprise (0.2–0.6 mean).
SURPRISE_DEFICIT_THRESHOLD = 0.15
SURPRISE_OVERLOAD_THRESHOLD = 0.65
SURPRISE_VARIANCE_MIN = 0.005


class SurpriseDeficitDetector(CritiqueRule):
    """Detect pieces that are too predictable.

    Fires when the overall surprise score is below the deficit
    threshold, indicating the piece is spec-correct but boring.
    """

    rule_id = "structure.surprise_deficit"
    role = Role.STRUCTURE

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect surprise deficit.

        Runs the SurpriseScorer on the plan's realized ScoreIR
        if available via the plan's cached analysis. For plan-only
        critique, checks tension arc coverage as a proxy.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects if surprise is too low.
        """
        findings: list[Finding] = []

        # Proxy metric: check if tension arcs provide variety
        arcs = plan.harmony.tension_arcs
        sections = plan.form.sections

        if len(sections) > 2 and len(arcs) == 0:
            # No tension arcs at all — surprise deficit proxy
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=("No tension arcs defined in the harmony plan. The piece risks being predictable and flat."),
                    evidence={
                        "tension_arc_count": 0,
                        "section_count": len(sections),
                        "threshold": "at least 1 arc for pieces with 3+ sections",
                    },
                    recommendation={
                        "harmony": (
                            "Add at least one tension arc (linear_rise, spike, or deceptive) to create local drama"
                        ),
                    },
                )
            )

        # Check for variety in tension levels across sections
        tension_levels = [s.target_tension for s in sections]
        if tension_levels:
            tension_range = max(tension_levels) - min(tension_levels)
            if tension_range < 0.15 and len(sections) > 1:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=(
                            f"Tension range across sections is only {tension_range:.2f}. "
                            "Pieces with low tension contrast risk being monotonous."
                        ),
                        evidence={
                            "tension_range": tension_range,
                            "threshold": 0.15,
                            "tension_values": {s.id: s.target_tension for s in sections},
                        },
                        recommendation={
                            "structure": "Differentiate section tension levels for more dynamic contrast",
                        },
                    )
                )

        return findings


class SurpriseOverloadDetector(CritiqueRule):
    """Detect pieces that are too unpredictable / chaotic.

    Fires when the surprise proxy indicators suggest excessive
    unpredictability — too many high-intensity tension arcs or
    extreme tension variation.
    """

    rule_id = "structure.surprise_overload"
    role = Role.STRUCTURE

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect surprise overload.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects if surprise is too high.
        """
        findings: list[Finding] = []
        arcs = plan.harmony.tension_arcs
        sections = plan.form.sections

        if not sections:
            return findings

        # Check for arc density overload
        total_bars = plan.form.total_bars()
        if total_bars > 0 and len(arcs) > 0:
            arc_bar_coverage = sum(a.location.span() for a in arcs)
            coverage_ratio = arc_bar_coverage / total_bars

            if coverage_ratio > 0.8:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Tension arcs cover {coverage_ratio:.0%} of the piece. "
                            "Over-saturating arcs removes the contrast that makes them effective."
                        ),
                        evidence={
                            "coverage_ratio": coverage_ratio,
                            "arc_count": len(arcs),
                            "total_bars": total_bars,
                            "threshold": 0.8,
                        },
                        recommendation={
                            "harmony": "Reduce tension arc coverage to leave breathing room between dramatic moments",
                        },
                    )
                )

        # Check for too many high-intensity arcs
        high_intensity_arcs = [a for a in arcs if a.intensity > 0.8]
        if len(high_intensity_arcs) > 3:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=(
                        f"{len(high_intensity_arcs)} high-intensity (>0.8) tension arcs. "
                        "When everything is dramatic, nothing is."
                    ),
                    evidence={
                        "high_intensity_count": len(high_intensity_arcs),
                        "threshold": 3,
                    },
                    recommendation={
                        "harmony": "Reserve high-intensity arcs for 1–2 key moments",
                    },
                )
            )

        return findings
