"""Harmonic critique rules — analyze chord progression issues.

Rules in this module detect problems with harmony: cliche progressions,
weak cadences, parallel fifths, missing secondary dominants, etc.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation

# Known cliche progressions (as Roman numeral tuples)
_CLICHE_PROGRESSIONS: list[tuple[str, ...]] = [
    ("I", "V", "vi", "IV"),
    ("vi", "IV", "I", "V"),
    ("I", "IV", "V", "I"),
    ("I", "vi", "IV", "V"),
]


class ClicheChordProgressionDetector(CritiqueRule):
    """Detect overused chord progressions repeated without variation.

    Flags when a 4-chord cliche pattern (I-V-vi-IV, etc.) appears
    3+ times consecutively without any variation.
    """

    rule_id = "harmonic.cliche_progression"
    role = Role.HARMONY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect cliche progressions."""
        findings: list[Finding] = []

        for section in plan.form.sections:
            chords = plan.harmony.chords_in_section(section.id)
            if len(chords) < 4:  # noqa: PLR2004
                continue

            romans = [c.roman for c in chords]
            for cliche in _CLICHE_PROGRESSIONS:
                consecutive_matches = 0
                i = 0
                while i + len(cliche) <= len(romans):
                    window = tuple(romans[i : i + len(cliche)])
                    if window == cliche:
                        consecutive_matches += 1
                        i += len(cliche)
                    else:
                        if consecutive_matches >= 3:  # noqa: PLR2004
                            break
                        consecutive_matches = 0
                        i += 1

                if consecutive_matches >= 3:  # noqa: PLR2004
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=Severity.MAJOR,
                            role=self.role,
                            issue=(
                                f"Section '{section.id}' uses "
                                f"{'-'.join(cliche)} {consecutive_matches} times consecutively"
                            ),
                            evidence={
                                "progression": list(cliche),
                                "count": consecutive_matches,
                                "threshold": 3,
                            },
                            location=SongLocation(section=section.id),
                            recommendation={
                                "harmony": "Introduce variation: V/V, bVII, or modal interchange",
                            },
                        )
                    )

        return findings


class CadenceWeaknessDetector(CritiqueRule):
    """Detect sections without proper cadential closure.

    Sections should typically end with a cadence (authentic, half, etc.).
    Missing cadences make sections feel incomplete.
    """

    rule_id = "harmonic.cadence_weakness"
    role = Role.HARMONY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect missing cadences."""
        findings: list[Finding] = []

        for section in plan.form.sections:
            cadence = plan.harmony.section_cadence(section.id)

            if cadence is None:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=f"Section '{section.id}' has no assigned cadence",
                        evidence={"section_id": section.id, "cadence": None},
                        location=SongLocation(section=section.id),
                        recommendation={
                            "harmony": (
                                f"Assign a cadence to '{section.id}': authentic for endings, half for continuations"
                            ),
                        },
                    )
                )

        return findings


class HarmonicMonotonyDetector(CritiqueRule):
    """Detect harmonic monotony — too few unique chords used in a section.

    If a section with 8+ bars uses only 2 or fewer unique chords,
    the harmony feels static.
    """

    rule_id = "harmonic.monotony"
    role = Role.HARMONY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect harmonic monotony."""
        findings: list[Finding] = []

        for section in plan.form.sections:
            if section.bars < 8:  # noqa: PLR2004
                continue

            chords = plan.harmony.chords_in_section(section.id)
            unique_romans = set(c.roman for c in chords)

            if len(unique_romans) <= 2:  # noqa: PLR2004
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Section '{section.id}' ({section.bars} bars) uses only "
                            f"{len(unique_romans)} unique chord(s): {sorted(unique_romans)}"
                        ),
                        evidence={
                            "unique_chords": len(unique_romans),
                            "section_bars": section.bars,
                            "chords": sorted(unique_romans),
                        },
                        location=SongLocation(section=section.id),
                        recommendation={
                            "harmony": "Add chord variety: secondary dominants, substitutions",
                        },
                    )
                )

        return findings
