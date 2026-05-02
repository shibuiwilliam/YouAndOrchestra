"""Arrangement critique rules — analyze orchestration issues.

Rules in this module detect problems with how instruments are arranged:
frequency collisions, texture collapse (all parts moving in unison), etc.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.ir.plan.arrangement import InstrumentRole
from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


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


class EnsembleRegisterViolationDetector(CritiqueRule):
    """Detect when arrangement assigns overlapping registers without separation.

    When two non-bass instruments are assigned to the same register band
    (< 12 semitones apart), they risk frequency masking.
    The Orchestrator should maintain register separation.

    Wave 3.2: EnsembleConstraint integration.
    """

    rule_id = "arrangement.ensemble_register_violation"
    role = Role.ARRANGEMENT

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect register overlap in arrangement assignments."""
        findings: list[Finding] = []

        if plan.arrangement is None:
            return findings

        # Group assignments by section
        sections: dict[str, list[tuple[str, int, int, str]]] = {}
        for a in plan.arrangement.assignments:
            if a.role == InstrumentRole.SILENT:
                continue
            sections.setdefault(a.section_id, []).append((a.instrument, a.register_low, a.register_high, a.role.value))

        for section_id, instruments in sections.items():
            if len(instruments) < 2:
                continue

            for i, (name_a, low_a, high_a, role_a) in enumerate(instruments):
                for name_b, low_b, high_b, role_b in instruments[i + 1 :]:
                    # Skip if either is the full range (unassigned)
                    if (low_a == 0 and high_a == 127) or (low_b == 0 and high_b == 127):
                        continue

                    # Check overlap
                    overlap_low = max(low_a, low_b)
                    overlap_high = min(high_a, high_b)
                    if overlap_high <= overlap_low:
                        continue

                    overlap_size = overlap_high - overlap_low
                    smaller_range = min(high_a - low_a, high_b - low_b)
                    if smaller_range <= 0:
                        continue

                    overlap_ratio = overlap_size / smaller_range
                    if overlap_ratio > 0.7:
                        findings.append(
                            Finding(
                                rule_id=self.rule_id,
                                severity=Severity.MINOR,
                                role=self.role,
                                issue=(
                                    f"Instruments '{name_a}' ({role_a}) and '{name_b}' ({role_b}) "
                                    f"have {overlap_ratio:.0%} register overlap in section '{section_id}'. "
                                    f"Risk of frequency masking."
                                ),
                                evidence={
                                    "section": section_id,
                                    "instrument_a": name_a,
                                    "instrument_b": name_b,
                                    "register_a": f"{low_a}-{high_a}",
                                    "register_b": f"{low_b}-{high_b}",
                                    "overlap_ratio": overlap_ratio,
                                },
                                location=SongLocation(section=section_id),
                                recommendation={
                                    "arrangement": (
                                        f"Separate registers: assign '{name_a}' and '{name_b}' "
                                        f"to non-overlapping octave bands."
                                    ),
                                },
                            )
                        )
        return findings
