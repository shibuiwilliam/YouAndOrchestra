"""Structured quality evaluation — implements PROJECT.md §9.

Evaluates generated compositions across five dimensions: structure, melody,
harmony, arrangement, and acoustics. Each metric is evaluated against a
MetricGoal (v2.0 Pillar 1) that defines the appropriate judgment mode.

The external interface (EvaluationScore, EvaluationReport, evaluate_score)
is preserved from v1 for backward compatibility.

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
from yao.verify.metric_goal import MetricGoal, MetricGoalType, evaluate_metric

# Dimension weights for user-facing quality score.
# Melody and harmony are most perceptible to listeners.
# v3.0 Wave 2.2: added aesthetic dimension.
_DIMENSION_WEIGHTS: dict[str, float] = {
    "structure": 0.20,
    "melody": 0.25,
    "harmony": 0.20,
    "aesthetic": 0.20,
    "arrangement": 0.10,
    "acoustics": 0.05,
}


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

    dimension: Literal["structure", "melody", "harmony", "aesthetic", "arrangement", "acoustics"]
    metric: str
    score: float
    target: float
    tolerance: float
    detail: str

    @property
    def passed(self) -> bool:
        """Whether the score meets the evaluation goal."""
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

    @property
    def quality_score(self) -> float:
        """Aggregate quality score (1.0–10.0) for user-facing display.

        Weights dimensions: melody 30%, harmony 25%, structure 25%,
        arrangement 10%, acoustics 10%. Empty reports return 5.0.

        Returns:
            Score between 1.0 and 10.0.
        """
        if not self.scores:
            return 5.0

        dim_averages: dict[str, float] = {}
        dim_counts: dict[str, int] = {}
        for s in self.scores:
            dim_averages[s.dimension] = dim_averages.get(s.dimension, 0.0) + s.score
            dim_counts[s.dimension] = dim_counts.get(s.dimension, 0) + 1

        weighted_sum = 0.0
        total_weight = 0.0
        for dim, weight in _DIMENSION_WEIGHTS.items():
            if dim in dim_averages:
                avg = dim_averages[dim] / dim_counts[dim]
                weighted_sum += avg * weight
                total_weight += weight

        if total_weight == 0.0:
            return 5.0

        normalized = weighted_sum / total_weight
        return 1.0 + normalized * 9.0

    def to_json(self) -> str:
        """Serialize the report to a JSON string.

        Returns:
            JSON string with all evaluation data.
        """
        data = asdict(self)
        data["quality_score"] = round(self.quality_score, 1)
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
            f"Quality Score: {self.quality_score:.1f}/10",
            f"Pass rate: {self.pass_rate:.0%} ({sum(1 for s in self.scores if s.passed)}/{len(self.scores)})",
        ]
        for dim in ("structure", "melody", "harmony", "aesthetic", "arrangement", "acoustics"):
            dim_scores = [s for s in self.scores if s.dimension == dim]
            if not dim_scores:
                continue
            lines.append(f"\n  [{dim.upper()}]")
            for s in dim_scores:
                status = "PASS" if s.passed else "FAIL"
                lines.append(
                    f"    {status} {s.metric}: {s.score:.2f} (target: {s.target:.2f} ±{s.tolerance:.2f}) — {s.detail}"
                )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal: MetricGoal-based evaluation helpers
# ---------------------------------------------------------------------------


def _score_via_goal(
    dimension: Literal["structure", "melody", "harmony", "aesthetic", "arrangement", "acoustics"],
    metric: str,
    value: float,
    goal: MetricGoal,
) -> EvaluationScore:
    """Evaluate a value against a MetricGoal, returning a legacy EvaluationScore.

    This bridges the v2 MetricGoal system to the v1 EvaluationScore interface.
    """
    result = evaluate_metric(metric, value, goal)

    # Map back to the v1 target/tolerance interface for backward compat
    if goal.type == MetricGoalType.TARGET_BAND:
        target = goal.target if goal.target is not None else 0.5
        tolerance = goal.tolerance
    elif goal.type == MetricGoalType.AT_LEAST:
        # "at least X" → target=1.0, tolerance = 1.0 - X
        target = 1.0
        tolerance = 1.0 - (goal.min_value or 0.0)
    elif goal.type == MetricGoalType.AT_MOST:
        # "at most X" → target=0.0, tolerance = X
        target = 0.0
        tolerance = goal.max_value or 1.0
    elif goal.type == MetricGoalType.BETWEEN:
        # "between A and B" → target=midpoint, tolerance=half-range
        lo = goal.min_value or 0.0
        hi = goal.max_value or 1.0
        target = (lo + hi) / 2.0
        tolerance = (hi - lo) / 2.0
    else:
        target = 0.5
        tolerance = 0.5

    # Override passed from MetricGoal result (more accurate than tolerance check)
    score_val = value
    detail = result.explanation

    return EvaluationScore(
        dimension=dimension,
        metric=metric,
        score=score_val,
        target=target,
        tolerance=tolerance,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Evaluation functions — now using MetricGoal internally
# ---------------------------------------------------------------------------


def evaluate_structure(
    score: ScoreIR,
    spec: CompositionSpec,
    trajectory: TrajectorySpec | None = None,
) -> list[EvaluationScore]:
    """Evaluate structural quality.

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
            _score_via_goal(
                "structure",
                "section_contrast",
                avg_contrast,
                MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.1, max_value=0.9),
            )
        )

    # Bar count accuracy
    spec_bars = spec.computed_total_bars()
    actual_bars = score.total_bars()
    bar_accuracy = 1.0 - abs(spec_bars - actual_bars) / max(spec_bars, 1)
    results.append(
        _score_via_goal(
            "structure",
            "bar_count_accuracy",
            max(0.0, bar_accuracy),
            MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.95),
        )
    )

    # Section count match
    spec_sections = len(spec.sections)
    actual_sections = len(score.sections)
    section_match = 1.0 if spec_sections == actual_sections else 0.0
    results.append(
        _score_via_goal(
            "structure",
            "section_count_match",
            section_match,
            MetricGoal(type=MetricGoalType.AT_LEAST, min_value=1.0),
        )
    )

    return results


def evaluate_melody(score: ScoreIR) -> list[EvaluationScore]:
    """Evaluate melodic quality.

    Args:
        score: The ScoreIR to evaluate.

    Returns:
        List of melody evaluation scores.
    """
    results: list[EvaluationScore] = []
    all_notes = score.all_notes()
    if not all_notes:
        return results

    # Pitch range utilization (per-instrument)
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
    range_score = max(0.0, 1.0 - abs(avg_range - 18.0) / 24.0)
    results.append(
        _score_via_goal(
            "melody",
            "pitch_range_utilization",
            range_score,
            MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=1.0),
        )
    )

    # Stepwise motion and contour variety (per-instrument)
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

        for i in range(len(instr_notes) - 1):
            interval = abs(instr_notes[i + 1].pitch - instr_notes[i].pitch)
            total_intervals += 1
            if interval <= 2:  # noqa: PLR2004
                total_stepwise += 1

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
            _score_via_goal(
                "melody",
                "stepwise_motion_ratio",
                stepwise_ratio,
                MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=0.9),
            )
        )

    if total_possible_changes > 0:
        contour_score = total_direction_changes / total_possible_changes
        results.append(
            _score_via_goal(
                "melody",
                "contour_variety",
                contour_score,
                MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.1, max_value=0.7),
            )
        )

    return results


def evaluate_harmony(score: ScoreIR) -> list[EvaluationScore]:
    """Evaluate harmonic quality.

    Args:
        score: The ScoreIR to evaluate.

    Returns:
        List of harmony evaluation scores.
    """
    results: list[EvaluationScore] = []
    all_notes = score.all_notes()
    if not all_notes:
        return results

    # Pitch class variety
    pitch_classes = set(n.pitch % 12 for n in all_notes)
    pc_variety = len(pitch_classes) / 12.0
    results.append(
        _score_via_goal(
            "harmony",
            "pitch_class_variety",
            pc_variety,
            MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=1.0),
        )
    )

    # Consonance ratio
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
        if pair_count == 0:
            return results
        consonance_ratio = consonance_count / pair_count
        # v2 fix: consonance uses AT_LEAST instead of TARGET_BAND.
        # "Consonance ratio too high" is not a meaningful failure.
        results.append(
            _score_via_goal(
                "harmony",
                "consonance_ratio",
                consonance_ratio,
                MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.4),
            )
        )

    return results


def evaluate_rhythm(score: ScoreIR) -> list[EvaluationScore]:
    """Evaluate rhythmic complexity and variety.

    Args:
        score: The ScoreIR to evaluate.

    Returns:
        List of EvaluationScore for rhythm metrics.
    """
    results: list[EvaluationScore] = []
    all_notes = score.all_notes()
    if not all_notes:
        return results

    # Rhythm variety: number of unique duration values (capped at 8)
    unique_durations = {round(n.duration_beats, 3) for n in all_notes}
    variety = min(len(unique_durations) / 8.0, 1.0)
    results.append(
        _score_via_goal(
            "structure",
            "rhythm_variety",
            variety,
            MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.2),
        )
    )

    # Syncopation ratio: notes starting on off-beats
    offbeat_count = sum(1 for n in all_notes if abs(n.start_beat - round(n.start_beat)) > 0.01)
    syncopation = offbeat_count / len(all_notes)
    results.append(
        _score_via_goal(
            "structure",
            "syncopation_ratio",
            syncopation,
            MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.0, max_value=0.6),
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
    report.scores.extend(evaluate_rhythm(score))
    return report
