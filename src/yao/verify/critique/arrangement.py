"""Arrangement critique rules — analyze orchestration issues.

Rules in this module detect problems with how instruments are arranged:
frequency collisions, texture collapse (all parts moving in unison), etc.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity


class FrequencyCollisionDetector(CritiqueRule):
    """Detect instruments whose ranges overlap significantly.

    When two non-bass instruments share more than 70% of their pitch range,
    they risk masking each other in the mix (frequency collision).
    """

    rule_id = "arrangement.frequency_collision"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect instrument pairs with excessive range overlap."""
        findings: list[Finding] = []

        instruments = list(spec.arrangement.instruments.keys())
        if len(instruments) < 2:  # noqa: PLR2004
            return findings

        for i, name_a in enumerate(instruments):
            range_a = INSTRUMENT_RANGES.get(name_a)
            if range_a is None:
                continue
            for name_b in instruments[i + 1 :]:
                range_b = INSTRUMENT_RANGES.get(name_b)
                if range_b is None:
                    continue

                # Calculate overlap
                overlap_low = max(range_a.midi_low, range_b.midi_low)
                overlap_high = min(range_a.midi_high, range_b.midi_high)
                if overlap_high <= overlap_low:
                    continue

                overlap_size = overlap_high - overlap_low
                smaller_range = min(
                    range_a.midi_high - range_a.midi_low,
                    range_b.midi_high - range_b.midi_low,
                )
                if smaller_range <= 0:
                    continue

                overlap_ratio = overlap_size / smaller_range
                if overlap_ratio > 0.7:  # noqa: PLR2004
                    findings.append(
                        Finding(
                            rule_id=self.rule_id,
                            severity=Severity.MINOR,
                            role=self.role,
                            issue=(
                                f"Instruments '{name_a}' and '{name_b}' have "
                                f"{overlap_ratio:.0%} range overlap — risk of frequency masking"
                            ),
                            evidence={
                                "instrument_a": name_a,
                                "instrument_b": name_b,
                                "overlap_ratio": overlap_ratio,
                                "overlap_range": f"{overlap_low}-{overlap_high}",
                            },
                            recommendation={
                                "arrangement": (
                                    f"Separate '{name_a}' and '{name_b}' into different octaves, "
                                    "or assign different roles (melody vs pad)"
                                ),
                            },
                        )
                    )

        return findings


class TextureCollapseDetector(CritiqueRule):
    """Detect when all instruments play the same role in all sections.

    A composition where every section uses the same set of instrument roles
    lacks textural contrast — the arrangement sounds static even if the
    notes change.
    """

    rule_id = "arrangement.texture_collapse"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect lack of textural variety across sections."""
        findings: list[Finding] = []

        instruments = spec.arrangement.instruments
        if len(instruments) < 2:  # noqa: PLR2004
            return findings

        # Check if all instruments have the same role
        roles = {inst.role for inst in instruments.values()}
        if len(roles) == 1:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"All {len(instruments)} instruments have the same role ('{next(iter(roles))}'). "
                        "The arrangement lacks textural variety."
                    ),
                    evidence={
                        "instruments": list(instruments.keys()),
                        "roles": list(roles),
                    },
                    recommendation={
                        "arrangement": (
                            "Assign different roles: one melody, one bass, one harmony/pad. "
                            "Consider counter_melody for thicker texture."
                        ),
                    },
                )
            )

        return findings
