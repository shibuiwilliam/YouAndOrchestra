"""Structured quality evaluation — implements PROJECT.md §12.

Evaluates generated compositions across five dimensions: structure, melody,
harmony, arrangement, and acoustics. Each metric returns a normalized score
(0.0–1.0) with a target and tolerance.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from yao.errors import VerificationError
from yao.ir.score_ir import ScoreIR
from yao.schema.composition import CompositionSpec
from yao.schema.trajectory import TrajectorySpec


@dataclass(frozen=True)
class EvaluationScore:
    """A single evaluation metric result.

    Attributes:
        dimension: Category (structure, melody, harmony, arrangement, acoustics).
        metric: Specific metric name.
        score: Normalized score (0.0–1.0, higher is better).
        target: Expected target score.
        tolerance: Acceptable deviation from target.
        detail: Human-readable explanation.
    """

    dimension: Literal["structure", "melody", "harmony", "arrangement", "acoustics"]
    metric: str
    score: float
    target: float
    tolerance: float
    detail: str

    @property
    def passed(self) -> bool:
        """Whether the score is within tolerance of the target."""
        # Use a small epsilon to avoid floating-point boundary failures
        return abs(self.score - self.target) <= self.tolerance + 1e-9


@dataclass
class EvaluationReport:
    """Complete evaluation across all dimensions.

    Attributes:
        title: Composition title being evaluated.
        scores: List of individual metric scores.
    """

    title: str
    scores: list[EvaluationScore] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Whether all scores are within tolerance."""
        return all(s.passed for s in self.scores)

    @property
    def pass_rate(self) -> float:
        """Fraction of metrics that passed."""
        if not self.scores:
            return 1.0
        return sum(1 for s in self.scores if s.passed) / len(self.scores)

    def to_json(self) -> str:
        """Serialize the report to a JSON string.

        Returns:
            JSON string with all evaluation data.
        """
        data = asdict(self)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, path: Path) -> None:
        """Save the evaluation report to a JSON file.

        Args:
            path: Output file path.

        Raises:
            VerificationError: If saving fails.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(self.to_json())
        except OSError as e:
            raise VerificationError(f"Failed to save evaluation: {e}") from e

    def summary(self) -> str:
        """Human-readable evaluation summary.

        Returns:
            Multi-line summary string.
        """
        lines = [
            f"=== Evaluation: {self.title} ===",
            f"Pass rate: {self.pass_rate:.0%} "
            f"({sum(1 for s in self.scores if s.passed)}/{len(self.scores)})",
        ]
        for dim in ("structure", "melody", "harmony", "arrangement", "acoustics"):
            dim_scores = [s for s in self.scores if s.dimension == dim]
            if not dim_scores:
                continue
            lines.append(f"\n  [{dim.upper()}]")
            for s in dim_scores:
                status = "PASS" if s.passed else "FAIL"
                lines.append(
                    f"    {status} {s.metric}: {s.score:.2f} "
                    f"(target: {s.target:.2f} ±{s.tolerance:.2f}) — {s.detail}"
                )
        return "\n".join(lines)


def evaluate_structure(
    score: ScoreIR,
    spec: CompositionSpec,
    trajectory: TrajectorySpec | None = None,
) -> list[EvaluationScore]:
    """Evaluate structural quality (PROJECT.md §12.1).

    Args:
        score: The ScoreIR to evaluate.
        spec: The composition specification.
        trajectory: Optional trajectory for density matching.

    Returns:
        List of structural evaluation scores.
    """
    results: list[EvaluationScore] = []

    # Section contrast: note density ratio between adjacent sections
    if len(score.sections) >= 2:  # noqa: PLR2004
        contrasts: list[float] = []
        for i in range(len(score.sections) - 1):
            sec_a = score.sections[i]
            sec_b = score.sections[i + 1]
            notes_a = sum(len(p.notes) for p in sec_a.parts)
            notes_b = sum(len(p.notes) for p in sec_b.parts)
            bars_a = max(sec_a.bar_count, 1)
            bars_b = max(sec_b.bar_count, 1)
            density_a = notes_a / bars_a
            density_b = notes_b / bars_b
            if density_a > 0 and density_b > 0:
                ratio = max(density_a, density_b) / min(density_a, density_b)
                contrasts.append(min(ratio / 2.0, 1.0))

        avg_contrast = sum(contrasts) / len(contrasts) if contrasts else 0.5
        results.append(
            EvaluationScore(
                dimension="structure",
                metric="section_contrast",
                score=avg_contrast,
                target=0.5,
                tolerance=0.4,
                detail=f"Avg density ratio: {avg_contrast:.2f}",
            )
        )

    # Bar count accuracy
    spec_bars = spec.computed_total_bars()
    actual_bars = score.total_bars()
    bar_accuracy = 1.0 - abs(spec_bars - actual_bars) / max(spec_bars, 1)
    results.append(
        EvaluationScore(
            dimension="structure",
            metric="bar_count_accuracy",
            score=max(0.0, bar_accuracy),
            target=1.0,
            tolerance=0.05,
            detail=f"Spec: {spec_bars} bars, actual: {actual_bars} bars",
        )
    )

    # Section count match
    spec_sections = len(spec.sections)
    actual_sections = len(score.sections)
    section_match = 1.0 if spec_sections == actual_sections else 0.0
    results.append(
        EvaluationScore(
            dimension="structure",
            metric="section_count_match",
            score=section_match,
            target=1.0,
            tolerance=0.0,
            detail=f"Spec: {spec_sections} sections, actual: {actual_sections}",
        )
    )

    return results


def evaluate_melody(score: ScoreIR) -> list[EvaluationScore]:
    """Evaluate melodic quality (PROJECT.md §12.2).

    Args:
        score: The ScoreIR to evaluate.

    Returns:
        List of melody evaluation scores.
    """
    results: list[EvaluationScore] = []
    all_notes = score.all_notes()
    if not all_notes:
        return results

    # Pitch range utilization: per-instrument melodic range check
    # A good melody typically spans 1-2 octaves (12-24 semitones).
    # We measure per instrument to avoid inflating range by combining
    # bass (C2) and melody (C5) instruments into one 47-semitone span.
    instrument_ranges: list[int] = []
    instruments_in_score: set[str] = set()
    for note in all_notes:
        instruments_in_score.add(note.instrument)
    for instr in instruments_in_score:
        instr_notes = [n for n in all_notes if n.instrument == instr]
        if instr_notes:
            instr_pitches = [n.pitch for n in instr_notes]
            instrument_ranges.append(max(instr_pitches) - min(instr_pitches))
    avg_range = sum(instrument_ranges) / max(len(instrument_ranges), 1)
    # Ideal range is ~12-24 semitones (1-2 octaves). Score peaks at 18.
    # Use a bell curve: distance from 18 semitones, normalized
    range_score = max(0.0, 1.0 - abs(avg_range - 18.0) / 24.0)
    results.append(
        EvaluationScore(
            dimension="melody",
            metric="pitch_range_utilization",
            score=range_score,
            target=0.7,
            tolerance=0.3,
            detail=f"Avg per-instrument range: {avg_range:.0f} semitones",
        )
    )

    # Stepwise motion and contour variety: computed per-instrument then averaged.
    # Mixing all instruments together produces nonsensical intervals
    # (e.g., bass C2 → melody C5 is not a meaningful melodic interval).
    total_stepwise = 0
    total_intervals = 0
    total_direction_changes = 0
    total_possible_changes = 0

    for instr in instruments_in_score:
        instr_notes = sorted(
            (n for n in all_notes if n.instrument == instr),
            key=lambda n: n.start_beat,
        )
        if len(instr_notes) < 2:  # noqa: PLR2004
            continue

        # Stepwise motion for this instrument
        for i in range(len(instr_notes) - 1):
            interval = abs(instr_notes[i + 1].pitch - instr_notes[i].pitch)
            total_intervals += 1
            if interval <= 2:  # noqa: PLR2004
                total_stepwise += 1

        # Contour variety for this instrument
        if len(instr_notes) >= 3:  # noqa: PLR2004
            for i in range(len(instr_notes) - 2):
                motion_a = instr_notes[i + 1].pitch - instr_notes[i].pitch
                motion_b = instr_notes[i + 2].pitch - instr_notes[i + 1].pitch
                total_possible_changes += 1
                if motion_a != 0 and motion_b != 0 and (motion_a > 0) != (motion_b > 0):
                    total_direction_changes += 1

    if total_intervals > 0:
        stepwise_ratio = total_stepwise / total_intervals
        results.append(
            EvaluationScore(
                dimension="melody",
                metric="stepwise_motion_ratio",
                score=stepwise_ratio,
                target=0.6,
                tolerance=0.3,
                detail=f"{total_stepwise}/{total_intervals} intervals are stepwise",
            )
        )

    if total_possible_changes > 0:
        contour_score = total_direction_changes / total_possible_changes
        results.append(
            EvaluationScore(
                dimension="melody",
                metric="contour_variety",
                score=contour_score,
                target=0.4,
                tolerance=0.3,
                detail=(
                    f"{total_direction_changes} direction changes "
                    f"in {len(all_notes)} notes"
                ),
            )
        )

    return results


def evaluate_harmony(score: ScoreIR) -> list[EvaluationScore]:
    """Evaluate harmonic quality (PROJECT.md §12.3).

    Args:
        score: The ScoreIR to evaluate.

    Returns:
        List of harmony evaluation scores.
    """
    results: list[EvaluationScore] = []
    all_notes = score.all_notes()
    if not all_notes:
        return results

    # Pitch class variety: how many of the 12 pitch classes are used
    pitch_classes = set(n.pitch % 12 for n in all_notes)
    pc_variety = len(pitch_classes) / 12.0
    results.append(
        EvaluationScore(
            dimension="harmony",
            metric="pitch_class_variety",
            score=pc_variety,
            target=0.5,
            tolerance=0.3,
            detail=f"{len(pitch_classes)}/12 pitch classes used",
        )
    )

    # Consonance ratio: fraction of notes that are consonant intervals
    # from the root (intervals: unison, 3rd, 4th, 5th, octave)
    consonant_intervals = {0, 3, 4, 5, 7, 8, 9, 12}
    if len(all_notes) >= 2:  # noqa: PLR2004
        consonance_count = 0
        pair_count = 0
        for i in range(len(all_notes)):
            for j in range(i + 1, min(i + 5, len(all_notes))):
                if abs(all_notes[i].start_beat - all_notes[j].start_beat) < 0.01:
                    interval = abs(all_notes[j].pitch - all_notes[i].pitch) % 12
                    pair_count += 1
                    if interval in consonant_intervals:
                        consonance_count += 1
        # Skip this metric if no simultaneous notes (e.g., solo instrument)
        if pair_count == 0:
            return results
        consonance_ratio = consonance_count / pair_count
        results.append(
            EvaluationScore(
                dimension="harmony",
                metric="consonance_ratio",
                score=consonance_ratio,
                target=0.7,
                tolerance=0.3,
                detail=f"{consonance_count}/{pair_count} simultaneous intervals consonant",
            )
        )

    return results


def evaluate_score(
    score: ScoreIR,
    spec: CompositionSpec,
    trajectory: TrajectorySpec | None = None,
) -> EvaluationReport:
    """Run all evaluators on a ScoreIR.

    Args:
        score: The ScoreIR to evaluate.
        spec: The composition specification.
        trajectory: Optional trajectory specification.

    Returns:
        Complete EvaluationReport.
    """
    report = EvaluationReport(title=score.title)
    report.scores.extend(evaluate_structure(score, spec, trajectory))
    report.scores.extend(evaluate_melody(score))
    report.scores.extend(evaluate_harmony(score))
    return report
