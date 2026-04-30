"""MetricGoal type system — polymorphic evaluation goals.

Replaces the v1 single ``abs(score - target) <= tolerance`` check with
7 typed judgment modes. This is Pillar 1 of the v2.0 verification system
(PROJECT.md §9.1).

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from yao.errors import VerificationError


class MetricGoalType(StrEnum):
    """The 7 evaluation judgment modes."""

    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    TARGET_BAND = "target_band"
    BETWEEN = "between"
    MATCH_CURVE = "match_curve"
    RELATIVE_ORDER = "relative_order"
    DIVERSITY = "diversity"


@dataclass(frozen=True)
class MetricGoal:
    """A typed evaluation goal.

    Field usage depends on ``type``:
      - AT_LEAST: ``min_value`` required.
      - AT_MOST: ``max_value`` required.
      - TARGET_BAND: ``target`` and ``tolerance`` required.
      - BETWEEN: ``min_value`` and ``max_value`` required.
      - MATCH_CURVE: ``target_curve`` and ``tolerance`` required.
      - RELATIVE_ORDER: ``expected_order`` required.
      - DIVERSITY: ``min_variance`` required.
    """

    type: MetricGoalType
    target: float | None = None
    tolerance: float = 0.0
    min_value: float | None = None
    max_value: float | None = None
    target_curve: tuple[tuple[float, float], ...] | None = None
    expected_order: tuple[str, ...] | None = None
    min_variance: float | None = None

    def __post_init__(self) -> None:
        """Validate that required fields are set for the chosen type."""
        t = self.type
        if t == MetricGoalType.AT_LEAST and self.min_value is None:
            raise VerificationError("AT_LEAST goal requires min_value")
        if t == MetricGoalType.AT_MOST and self.max_value is None:
            raise VerificationError("AT_MOST goal requires max_value")
        if t == MetricGoalType.TARGET_BAND and self.target is None:
            raise VerificationError("TARGET_BAND goal requires target")
        if t == MetricGoalType.BETWEEN and (self.min_value is None or self.max_value is None):
            raise VerificationError("BETWEEN goal requires min_value and max_value")
        if t == MetricGoalType.MATCH_CURVE and self.target_curve is None:
            raise VerificationError("MATCH_CURVE goal requires target_curve")
        if t == MetricGoalType.RELATIVE_ORDER and self.expected_order is None:
            raise VerificationError("RELATIVE_ORDER goal requires expected_order")
        if t == MetricGoalType.DIVERSITY and self.min_variance is None:
            raise VerificationError("DIVERSITY goal requires min_variance")


@dataclass(frozen=True)
class MetricEvaluation:
    """Result of evaluating a single metric against a MetricGoal.

    Attributes:
        metric_name: Name of the metric.
        actual_value: The measured value(s).
        goal: The goal that was evaluated against.
        passed: Whether the goal was met.
        distance: How far from passing (0.0 if passed).
        explanation: Human-readable explanation.
    """

    metric_name: str
    actual_value: Any
    goal: MetricGoal
    passed: bool
    distance: float
    explanation: str


# ---------------------------------------------------------------------------
# Evaluation dispatch
# ---------------------------------------------------------------------------

_EPSILON = 1e-9


def evaluate_metric(
    metric_name: str,
    value: Any,
    goal: MetricGoal,
) -> MetricEvaluation:
    """Evaluate a metric value against a goal.

    Single dispatch on ``goal.type``.

    Args:
        metric_name: Name of the metric.
        value: The measured value. Type depends on goal type:
            - AT_LEAST, AT_MOST, TARGET_BAND, BETWEEN: float
            - MATCH_CURVE: list of (position, value) tuples
            - RELATIVE_ORDER: list of (name, value) tuples
            - DIVERSITY: list of float values
        goal: The evaluation goal.

    Returns:
        MetricEvaluation with pass/fail and explanation.
    """
    dispatch = _DISPATCH.get(goal.type)
    if dispatch is None:
        raise VerificationError(f"Unknown MetricGoalType: {goal.type}")
    passed, distance, explanation = dispatch(value, goal)
    return MetricEvaluation(
        metric_name=metric_name,
        actual_value=value,
        goal=goal,
        passed=passed,
        distance=distance,
        explanation=explanation,
    )


def _eval_at_least(value: float, goal: MetricGoal) -> tuple[bool, float, str]:
    """Value must be >= min_value."""
    assert goal.min_value is not None
    passed = value >= goal.min_value - _EPSILON
    distance = max(0.0, goal.min_value - value)
    status = "meets" if passed else "below"
    return passed, distance, f"{value:.3f} {status} threshold {goal.min_value:.3f}"


def _eval_at_most(value: float, goal: MetricGoal) -> tuple[bool, float, str]:
    """Value must be <= max_value."""
    assert goal.max_value is not None
    passed = value <= goal.max_value + _EPSILON
    distance = max(0.0, value - goal.max_value)
    status = "meets" if passed else "above"
    return passed, distance, f"{value:.3f} {status} ceiling {goal.max_value:.3f}"


def _eval_target_band(value: float, goal: MetricGoal) -> tuple[bool, float, str]:
    """Value must be within tolerance of target."""
    assert goal.target is not None
    deviation = abs(value - goal.target)
    passed = deviation <= goal.tolerance + _EPSILON
    distance = max(0.0, deviation - goal.tolerance)
    status = "within" if passed else "outside"
    return (
        passed,
        distance,
        f"{value:.3f} {status} band {goal.target:.3f} ±{goal.tolerance:.3f}",
    )


def _eval_between(value: float, goal: MetricGoal) -> tuple[bool, float, str]:
    """Value must be within [min_value, max_value]."""
    assert goal.min_value is not None and goal.max_value is not None
    passed = goal.min_value - _EPSILON <= value <= goal.max_value + _EPSILON
    if value < goal.min_value:
        distance = goal.min_value - value
    elif value > goal.max_value:
        distance = value - goal.max_value
    else:
        distance = 0.0
    status = "within" if passed else "outside"
    return (
        passed,
        distance,
        f"{value:.3f} {status} [{goal.min_value:.3f}, {goal.max_value:.3f}]",
    )


def _eval_match_curve(
    values: list[tuple[float, float]],
    goal: MetricGoal,
) -> tuple[bool, float, str]:
    """Actual curve must follow target curve within tolerance.

    Both ``values`` and ``goal.target_curve`` are lists of (position, value).
    We interpolate the target at each actual position and compute mean
    absolute error.
    """
    assert goal.target_curve is not None
    if not values:
        return False, 1.0, "no data points to compare"

    target_pts = list(goal.target_curve)
    total_error = 0.0
    for pos, actual_val in values:
        expected = _interpolate(target_pts, pos)
        total_error += abs(actual_val - expected)

    mae = total_error / len(values)
    passed = mae <= goal.tolerance + _EPSILON
    distance = max(0.0, mae - goal.tolerance)
    status = "follows" if passed else "deviates from"
    return passed, distance, f"MAE {mae:.3f} {status} curve (tolerance {goal.tolerance:.3f})"


def _eval_relative_order(
    items: list[tuple[str, float]],
    goal: MetricGoal,
) -> tuple[bool, float, str]:
    """Items sorted by value must match expected_order.

    Only items named in expected_order are checked. Their relative order
    (ascending by value) must match the expected sequence.
    """
    assert goal.expected_order is not None
    expected = list(goal.expected_order)
    name_to_val = dict(items)

    # Filter to only names present in both expected_order and items
    relevant = [(name, name_to_val[name]) for name in expected if name in name_to_val]
    if len(relevant) < 2:  # noqa: PLR2004
        return True, 0.0, "fewer than 2 comparable items"

    # Check if values are in non-decreasing order
    violations = 0
    for i in range(len(relevant) - 1):
        if relevant[i][1] > relevant[i + 1][1] + _EPSILON:
            violations += 1

    passed = violations == 0
    distance = float(violations)
    if passed:
        return True, 0.0, f"order matches: {[r[0] for r in relevant]}"
    return (
        False,
        distance,
        f"{violations} order violation(s) in {[r[0] for r in relevant]}",
    )


def _eval_diversity(
    values: list[float],
    goal: MetricGoal,
) -> tuple[bool, float, str]:
    """Variance of values must be >= min_variance."""
    assert goal.min_variance is not None
    if len(values) < 2:  # noqa: PLR2004
        return False, goal.min_variance, "fewer than 2 values for diversity"

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    passed = variance >= goal.min_variance - _EPSILON
    distance = max(0.0, goal.min_variance - variance)
    status = "sufficient" if passed else "insufficient"
    return (
        passed,
        distance,
        f"variance {variance:.4f} {status} (min {goal.min_variance:.4f})",
    )


def _interpolate(points: list[tuple[float, float]], x: float) -> float:
    """Linear interpolation between sorted (x, y) points."""
    if not points:
        return 0.5
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= x <= x1:
            if x1 == x0:
                return y0
            frac = (x - x0) / (x1 - x0)
            return y0 + frac * (y1 - y0)
    return 0.5


# Dispatch table
_DISPATCH: dict[MetricGoalType, Any] = {
    MetricGoalType.AT_LEAST: _eval_at_least,
    MetricGoalType.AT_MOST: _eval_at_most,
    MetricGoalType.TARGET_BAND: _eval_target_band,
    MetricGoalType.BETWEEN: _eval_between,
    MetricGoalType.MATCH_CURVE: _eval_match_curve,
    MetricGoalType.RELATIVE_ORDER: _eval_relative_order,
    MetricGoalType.DIVERSITY: _eval_diversity,
}
