"""LoopabilityValidator — multi-dimensional loop boundary analysis.

Validates that a piece can loop seamlessly for game BGM, ambient,
and other loop-centric use cases. Checks rhythmic, harmonic, melodic,
and dynamic continuity at the loop boundary.

Goodhart defense: a trivially loopable piece (single sustained note)
scores perfectly on all continuity metrics but fails musical quality.
Cross-check with the Programmatic Critic's structural and melodic
coherence rules.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yao.ir.note import Note
    from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class LoopabilityReport:
    """Multi-dimensional assessment of loop-boundary quality.

    Each dimension is a score in [0.0, 1.0] where 1.0 = perfectly seamless.

    Attributes:
        rhythmic_continuity: Whether the rhythmic pattern flows across the boundary.
        harmonic_continuity: Whether the last chord resolves into the first chord.
        melodic_continuity: Whether the melody does not create awkward leaps at the seam.
        dynamic_continuity: Whether velocity does not jump abruptly at the boundary.
        overall: Weighted average of all dimensions.
        issues: List of human-readable descriptions of loop problems.
    """

    rhythmic_continuity: float
    harmonic_continuity: float
    melodic_continuity: float
    dynamic_continuity: float
    overall: float
    issues: tuple[str, ...]


class LoopabilityValidator:
    """Validates seamless looping by analyzing the join point.

    Conceptually concatenates the piece with itself and checks whether
    the seam is musically invisible.
    """

    def __init__(self, beats_per_bar: float = 4.0) -> None:
        """Initialize the validator.

        Args:
            beats_per_bar: Beats per bar for boundary calculation.
        """
        self._beats_per_bar = beats_per_bar

    def validate(self, score: ScoreIR) -> LoopabilityReport:
        """Validate loop-boundary quality for a ScoreIR.

        Args:
            score: The ScoreIR to validate.

        Returns:
            LoopabilityReport with per-dimension scores and issues.
        """
        notes = score.all_notes()
        issues: list[str] = []

        if not notes:
            return LoopabilityReport(
                rhythmic_continuity=1.0,
                harmonic_continuity=1.0,
                melodic_continuity=1.0,
                dynamic_continuity=1.0,
                overall=1.0,
                issues=(),
            )

        max_beat = max(n.start_beat + n.duration_beats for n in notes)
        boundary_window = self._beats_per_bar  # look at last bar + first bar

        # Notes near the end and near the start
        end_notes = [n for n in notes if n.start_beat >= max_beat - boundary_window]
        start_notes = [n for n in notes if n.start_beat < boundary_window]

        rhythmic = self._check_rhythmic(end_notes, start_notes, max_beat, issues)
        harmonic = self._check_harmonic(end_notes, start_notes, issues)
        melodic = self._check_melodic(end_notes, start_notes, issues)
        dynamic = self._check_dynamic(end_notes, start_notes, issues)

        overall = 0.30 * rhythmic + 0.25 * harmonic + 0.25 * melodic + 0.20 * dynamic

        return LoopabilityReport(
            rhythmic_continuity=rhythmic,
            harmonic_continuity=harmonic,
            melodic_continuity=melodic,
            dynamic_continuity=dynamic,
            overall=overall,
            issues=tuple(issues),
        )

    def _check_rhythmic(
        self,
        end_notes: list[Note],
        start_notes: list[Note],
        max_beat: float,
        issues: list[str],
    ) -> float:
        """Check rhythmic pattern continuity at the boundary.

        Compares onset density in the last bar vs the first bar.
        """
        if not end_notes and not start_notes:
            return 1.0

        end_density = len(end_notes)
        start_density = len(start_notes)

        if end_density == 0 or start_density == 0:
            if end_density == 0 and start_density == 0:
                return 1.0
            issues.append(f"Rhythmic gap at boundary: end_density={end_density}, start_density={start_density}")
            return 0.3

        ratio = min(end_density, start_density) / max(end_density, start_density)
        if ratio < 0.5:
            issues.append(f"Rhythmic density mismatch at boundary: {end_density} vs {start_density} notes")
        return ratio

    def _check_harmonic(
        self,
        end_notes: list[Note],
        start_notes: list[Note],
        issues: list[str],
    ) -> float:
        """Check harmonic compatibility at the boundary.

        Measures pitch-class overlap between the last and first beat groups.
        """
        if not end_notes or not start_notes:
            return 1.0

        end_pcs = {n.pitch % 12 for n in end_notes}
        start_pcs = {n.pitch % 12 for n in start_notes}

        if not end_pcs or not start_pcs:
            return 1.0

        overlap = len(end_pcs & start_pcs)
        total = len(end_pcs | start_pcs)
        jaccard = overlap / total if total > 0 else 1.0

        if jaccard < 0.3:
            issues.append("Harmonic clash at loop boundary: few shared pitch classes")

        return jaccard

    def _check_melodic(
        self,
        end_notes: list[Note],
        start_notes: list[Note],
        issues: list[str],
    ) -> float:
        """Check melodic continuity — no large leaps at the boundary.

        Measures the interval between the last note and the first note.
        """
        if not end_notes or not start_notes:
            return 1.0

        last_note = max(end_notes, key=lambda n: n.start_beat)
        first_note = min(start_notes, key=lambda n: n.start_beat)

        interval = abs(last_note.pitch - first_note.pitch)

        if interval > 12:
            issues.append(f"Large melodic leap at boundary: {interval} semitones")
            return float(max(0.0, 1.0 - (interval - 12) / 24.0))
        if interval > 7:
            issues.append(f"Moderate melodic leap at boundary: {interval} semitones")
            return 0.7

        return 1.0

    def _check_dynamic(
        self,
        end_notes: list[Note],
        start_notes: list[Note],
        issues: list[str],
    ) -> float:
        """Check dynamic (velocity) continuity at the boundary.

        A sudden velocity jump at the loop point creates an audible seam.
        """
        if not end_notes or not start_notes:
            return 1.0

        end_avg_vel = sum(n.velocity for n in end_notes) / len(end_notes)
        start_avg_vel = sum(n.velocity for n in start_notes) / len(start_notes)

        diff = abs(end_avg_vel - start_avg_vel)
        if diff > 30:
            issues.append(f"Dynamic jump at boundary: velocity diff={diff:.0f}")
            return float(max(0.0, 1.0 - diff / 80.0))

        return float(min(1.0, 1.0 - diff / 80.0))
