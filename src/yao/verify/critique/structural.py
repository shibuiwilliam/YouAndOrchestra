"""Structural critique rules — analyze form-level issues.

Rules in this module detect problems with the overall song structure:
monotonous sections, missing climax, form imbalance, etc.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class SectionMonotonyDetector(CritiqueRule):
    """Detect sections with too-similar tension/density profiles.

    If adjacent sections have nearly identical target_tension and
    target_density, the piece will feel static and undifferentiated.
    """

    rule_id = "structure.section_monotony"
    role = Role.STRUCTURE

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect monotonous section pairs."""
        findings: list[Finding] = []
        sections = plan.form.sections
        if len(sections) < 2:  # noqa: PLR2004
            return findings

        for i in range(len(sections) - 1):
            a, b = sections[i], sections[i + 1]
            tension_diff = abs(a.target_tension - b.target_tension)
            density_diff = abs(a.target_density - b.target_density)

            if tension_diff < 0.1 and density_diff < 0.1:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Sections '{a.id}' and '{b.id}' have nearly identical "
                            f"tension ({a.target_tension:.2f} vs {b.target_tension:.2f}) "
                            f"and density ({a.target_density:.2f} vs {b.target_density:.2f})"
                        ),
                        evidence={
                            "tension_diff": tension_diff,
                            "density_diff": density_diff,
                            "threshold": 0.1,
                        },
                        location=SongLocation(section=f"{a.id}/{b.id}"),
                        recommendation={
                            "structure": (f"Differentiate '{b.id}' by raising/lowering tension or density"),
                        },
                    )
                )

        return findings


class ClimaxAbsenceDetector(CritiqueRule):
    """Detect lack of a climax in the composition.

    A piece without any section marked as climax, or without a section
    whose tension exceeds 0.7, lacks a dynamic peak.
    """

    rule_id = "structure.climax_absence"
    role = Role.STRUCTURE

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect missing climax."""
        findings: list[Finding] = []
        sections = plan.form.sections

        has_climax = any(s.is_climax for s in sections)
        max_tension = max((s.target_tension for s in sections), default=0.0)

        if not has_climax and max_tension < 0.7:  # noqa: PLR2004
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"No section is marked as climax and max tension is only {max_tension:.2f} (threshold: 0.7)"
                    ),
                    evidence={
                        "has_climax_flag": has_climax,
                        "max_tension": max_tension,
                        "threshold": 0.7,
                    },
                    recommendation={
                        "structure": "Mark one section as climax with target_tension >= 0.7",
                    },
                )
            )

        return findings


class FormImbalanceDetector(CritiqueRule):
    """Detect grossly disproportionate section lengths.

    If one section is more than 4x longer than the shortest section,
    the form may feel unbalanced.
    """

    rule_id = "structure.form_imbalance"
    role = Role.STRUCTURE

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect form imbalance."""
        findings: list[Finding] = []
        sections = plan.form.sections
        if len(sections) < 2:  # noqa: PLR2004
            return findings

        bar_counts = [s.bars for s in sections]
        shortest = min(bar_counts)
        longest = max(bar_counts)

        if shortest > 0 and longest / shortest > 4:  # noqa: PLR2004
            short_section = next(s for s in sections if s.bars == shortest)
            long_section = next(s for s in sections if s.bars == longest)
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=(
                        f"Section '{long_section.id}' ({longest} bars) is "
                        f"{longest / shortest:.1f}x longer than '{short_section.id}' "
                        f"({shortest} bars)"
                    ),
                    evidence={
                        "longest_bars": longest,
                        "shortest_bars": shortest,
                        "ratio": longest / shortest,
                        "threshold": 4.0,
                    },
                    location=SongLocation(section=long_section.id),
                    recommendation={
                        "structure": (f"Consider splitting '{long_section.id}' or extending '{short_section.id}'"),
                    },
                )
            )

        return findings
