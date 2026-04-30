"""Melodic critique rules — analyze melody-level issues.

Rules in this module detect problems with melodic content: contour
monotony, lack of motif recurrence, weak phrase endings, etc.

Note: These rules operate on the MusicalPlan, not the realized ScoreIR.
They primarily analyze MotifPlan and PhrasePlan when available.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class ContourMonotonyDetector(CritiqueRule):
    """Detect when the melodic contour barely changes across sections.

    Without contour variation, melodies feel flat and undifferentiated
    even if the notes change. This checks whether phrase contour types
    are diverse enough across sections.
    """

    rule_id = "melody.contour_monotony"
    role = Role.MELODY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect contour monotony in the phrase plan."""
        findings: list[Finding] = []

        if plan.phrase is None:
            return findings

        contours = [p.contour.value for p in plan.phrase.phrases]
        if len(contours) < 4:  # noqa: PLR2004
            return findings

        unique_contours = set(contours)
        variety_ratio = len(unique_contours) / len(contours)

        if variety_ratio < 0.3:  # noqa: PLR2004
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"Only {len(unique_contours)} unique contour(s) across "
                        f"{len(contours)} phrases (variety ratio: {variety_ratio:.2f})"
                    ),
                    evidence={
                        "unique_contours": list(unique_contours),
                        "total_phrases": len(contours),
                        "variety_ratio": variety_ratio,
                        "threshold": 0.3,
                    },
                    recommendation={
                        "melody": "Vary contour shapes: use arch, rise, fall, wave across sections",
                    },
                )
            )

        return findings


class MotifRecurrenceDetector(CritiqueRule):
    """Detect when motifs don't recur enough for memorability.

    A motif that appears only once cannot serve as a hook. Each seed motif
    should appear at least 3 times (including variations) across the piece.
    """

    rule_id = "melody.motif_recurrence"
    role = Role.MELODY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect insufficient motif recurrence."""
        findings: list[Finding] = []

        if plan.motif is None or not plan.motif.seeds:
            return findings

        for seed in plan.motif.seeds:
            count = plan.motif.recurrence_count(seed.id)
            if count < 3:  # noqa: PLR2004
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Motif '{seed.id}' ({seed.character or 'unnamed'}) "
                            f"appears only {count} time(s) (minimum: 3)"
                        ),
                        evidence={
                            "motif_id": seed.id,
                            "recurrence_count": count,
                            "threshold": 3,
                        },
                        recommendation={
                            "melody": (
                                f"Place motif '{seed.id}' in more sections with "
                                "variations (sequence, inversion, transposition)"
                            ),
                        },
                    )
                )

        return findings


class PhraseClosureWeaknessDetector(CritiqueRule):
    """Detect phrases that lack cadential closure.

    Consequent phrases should typically target an authentic cadence,
    and antecedent phrases should target a half cadence. Phrases with
    cadence='none' in structural roles feel incomplete.
    """

    rule_id = "melody.phrase_closure_weakness"
    role = Role.MELODY

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect weak phrase closures."""
        findings: list[Finding] = []

        if plan.phrase is None:
            return findings

        from yao.ir.plan.phrase import PhraseCadence, PhraseRole

        for phrase in plan.phrase.phrases:
            # Consequent phrases should have authentic or plagal cadence
            if phrase.role == PhraseRole.CONSEQUENT and phrase.cadence == PhraseCadence.NONE:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=(
                            f"Consequent phrase '{phrase.id}' in section '{phrase.section_id}' "
                            "has no cadence — expected authentic or plagal"
                        ),
                        evidence={
                            "phrase_id": phrase.id,
                            "phrase_role": phrase.role.value,
                            "cadence": phrase.cadence.value,
                        },
                        location=SongLocation(section=phrase.section_id),
                        recommendation={
                            "melody": "Assign authentic cadence to consequent phrases",
                        },
                    )
                )

        return findings
