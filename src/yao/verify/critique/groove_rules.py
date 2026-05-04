"""Groove critique rules — detect groove-related issues.

Rules in this module detect problems with ensemble groove:
- No groove defined when genre demands one
- Flat microtiming (no groove feel)
- Conflicting groove parameters

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity

# Genres that strongly benefit from groove
GROOVE_EXPECTED_GENRES = frozenset(
    {
        "jazz",
        "jazz_ballad",
        "lofi_hiphop",
        "funk",
        "bossa_nova",
        "reggae",
        "soul",
        "r&b",
        "hip_hop",
        "trap",
        "neo_soul",
    }
)


class GrooveInconsistencyDetector(CritiqueRule):
    """Detect when a genre expects groove but no groove profile is present.

    Fires when the piece's genre is typically groove-dependent but
    the MusicalPlan has no drum pattern with swing or humanize settings.
    """

    rule_id = "rhythm.groove_inconsistency"
    role = Role.RHYTHM

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect groove inconsistency.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects.
        """
        findings: list[Finding] = []
        genre = plan.global_context.genre.lower()

        if genre not in GROOVE_EXPECTED_GENRES:
            return findings

        # Check if there's any groove indication
        has_swing = False
        has_humanize = False
        if plan.drums is not None:
            has_swing = plan.drums.swing > 0.05
            has_humanize = plan.drums.humanize > 0.05

        if not has_swing and not has_humanize:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"Genre '{genre}' typically requires groove feel, but "
                        "drum pattern has no swing or humanization. "
                        "The piece may sound mechanical."
                    ),
                    evidence={
                        "genre": genre,
                        "drum_swing": plan.drums.swing if plan.drums else 0.0,
                        "drum_humanize": plan.drums.humanize if plan.drums else 0.0,
                    },
                    recommendation={
                        "rhythm": (f"Add a GrooveProfile matching '{genre}' or increase drum swing/humanize values"),
                    },
                )
            )

        return findings


class MicrotimingFlatnessDetector(CritiqueRule):
    """Detect when microtiming is completely flat across the piece.

    If all drum hits have zero microtiming and the piece has
    more than 16 bars, the groove will feel robotic.
    """

    rule_id = "rhythm.microtiming_flatness"
    role = Role.RHYTHM

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect flat microtiming.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects.
        """
        findings: list[Finding] = []

        if plan.drums is None:
            return findings

        total_bars = plan.form.total_bars()
        if total_bars < 16:
            return findings

        # Check if all drum hits have zero microtiming
        hits = plan.drums.hits
        if not hits:
            return findings

        all_zero = all(abs(h.microtiming_ms) < 0.1 for h in hits)
        no_humanize = plan.drums.humanize < 0.05

        if all_zero and no_humanize:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=(
                        f"All {len(hits)} drum hits have zero microtiming "
                        f"in a {total_bars}-bar piece. Consider adding "
                        "groove or humanization for a more natural feel."
                    ),
                    evidence={
                        "hit_count": len(hits),
                        "total_bars": total_bars,
                        "max_microtiming_ms": max(abs(h.microtiming_ms) for h in hits),
                        "humanize": plan.drums.humanize,
                    },
                    recommendation={
                        "rhythm": "Apply a GrooveProfile or increase humanize to >0.1",
                    },
                )
            )

        return findings


class EnsembleGrooveConflictDetector(CritiqueRule):
    """Detect conflicting groove parameters between drum pattern and global context.

    Fires when the drum pattern has high swing but the genre typically
    uses straight 16ths (or vice versa).
    """

    rule_id = "rhythm.ensemble_groove_conflict"
    role = Role.RHYTHM

    # Genres that should be straight (low swing)
    STRAIGHT_GENRES = frozenset(
        {
            "edm",
            "electronic",
            "techno",
            "house",
            "trance",
            "metal",
            "punk",
            "industrial",
        }
    )

    # Genres that should have swing
    SWING_GENRES = frozenset(
        {
            "jazz",
            "jazz_ballad",
            "blues",
            "swing",
            "shuffle",
        }
    )

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect groove conflicts.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects.
        """
        findings: list[Finding] = []

        if plan.drums is None:
            return findings

        genre = plan.global_context.genre.lower()
        swing = plan.drums.swing

        # High swing in a straight genre
        if genre in self.STRAIGHT_GENRES and swing > 0.3:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=(
                        f"Drum swing is {swing:.2f} but genre '{genre}' "
                        "typically uses straight timing. This may sound odd."
                    ),
                    evidence={
                        "genre": genre,
                        "swing": swing,
                        "expected_range": "< 0.3 for straight genres",
                    },
                    recommendation={
                        "rhythm": f"Reduce swing to < 0.1 for '{genre}' style",
                    },
                )
            )

        # No swing in a swing genre
        if genre in self.SWING_GENRES and swing < 0.2:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"Drum swing is only {swing:.2f} but genre '{genre}' "
                        "demands swing feel. The piece will sound stiff."
                    ),
                    evidence={
                        "genre": genre,
                        "swing": swing,
                        "expected_range": ">= 0.4 for swing genres",
                    },
                    recommendation={
                        "rhythm": f"Increase swing to >= 0.5 for '{genre}' style",
                    },
                )
            )

        return findings
