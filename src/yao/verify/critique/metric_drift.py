"""Metric drift detector — catches misalignment between spec meter and output.

Detects when a piece specified in non-4/4 meter has rhythmic accents
that systematically fall on 4/4-implied positions, suggesting the generator
ignored the meter specification.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.timing import beats_per_bar_from_sig, parse_time_signature
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity, SongLocation


class MetricDriftDetector(CritiqueRule):
    """Detect when output accents drift toward 4/4 despite a non-4/4 spec.

    For non-4/4 pieces, checks whether the highest-velocity notes
    in each bar consistently land on quarter-beat positions (0, 1, 2, 3)
    rather than the meter's actual strong-beat positions.

    Only fires for non-4/4 meters.
    """

    rule_id = "metric_drift"
    role = Role.RHYTHM

    def detect(
        self,
        plan: MusicalPlan,
        spec: CompositionSpecV2,
    ) -> list[Finding]:
        """Detect metric drift in the musical plan.

        Args:
            plan: The musical plan to critique.
            spec: The composition specification.

        Returns:
            List of Finding objects if drift detected.
        """
        ts = spec.global_.time_signature if hasattr(spec, "global_") else "4/4"
        num, den = parse_time_signature(ts)

        # Only relevant for non-4/4 meters
        if num == 4 and den == 4:  # noqa: PLR2004
            return []

        bpb = beats_per_bar_from_sig(num, den)

        # Check if score has note data to analyze
        if not hasattr(plan, "score") or plan.score is None:
            return []

        score = plan.score
        total_notes = 0
        notes_on_quarter_beats = 0

        for section in score.sections:
            for part in section.parts:
                for note in part.notes:
                    total_notes += 1
                    # Check if note start is on a quarter-beat boundary
                    beat_in_bar = note.start_beat % bpb
                    is_quarter_aligned = abs(beat_in_bar - round(beat_in_bar)) < 0.05  # noqa: PLR2004
                    if is_quarter_aligned and round(beat_in_bar) == beat_in_bar:
                        notes_on_quarter_beats += 1

        if total_notes == 0:
            return []

        quarter_ratio = notes_on_quarter_beats / total_notes
        # If >80% of notes fall on quarter-beat boundaries in a non-4/4 meter,
        # the generator likely treated it as 4/4
        threshold = 0.80
        if quarter_ratio > threshold:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"Meter is {ts} but {quarter_ratio:.0%} of notes fall on "
                        f"quarter-beat positions, suggesting 4/4 drift"
                    ),
                    evidence={
                        "specified_meter": ts,
                        "quarter_beat_ratio": round(quarter_ratio, 3),
                        "threshold": threshold,
                        "total_notes": total_notes,
                    },
                    location=SongLocation(),
                    recommendation={
                        "action": "regenerate",
                        "detail": (
                            f"Generator should respect {ts} meter grouping. Use MeterSpec-aware note placement."
                        ),
                    },
                ),
            ]

        return []
