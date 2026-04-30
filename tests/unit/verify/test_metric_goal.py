"""Tests for MetricGoal type system — all 7 goal types.

Each type gets at least 3 cases: pass, fail, boundary.
"""

from __future__ import annotations

import pytest

from yao.errors import VerificationError
from yao.verify.metric_goal import (
    MetricEvaluation,
    MetricGoal,
    MetricGoalType,
    evaluate_metric,
)

# ---------------------------------------------------------------------------
# AT_LEAST
# ---------------------------------------------------------------------------


class TestAtLeast:
    def test_pass(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.5)
        result = evaluate_metric("test", 0.7, goal)
        assert result.passed
        assert result.distance == 0.0

    def test_fail(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.5)
        result = evaluate_metric("test", 0.3, goal)
        assert not result.passed
        assert result.distance == pytest.approx(0.2)

    def test_boundary(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.5)
        result = evaluate_metric("test", 0.5, goal)
        assert result.passed

    def test_missing_min_value_raises(self) -> None:
        with pytest.raises(VerificationError, match="min_value"):
            MetricGoal(type=MetricGoalType.AT_LEAST)


# ---------------------------------------------------------------------------
# AT_MOST
# ---------------------------------------------------------------------------


class TestAtMost:
    def test_pass(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_MOST, max_value=0.8)
        result = evaluate_metric("test", 0.5, goal)
        assert result.passed
        assert result.distance == 0.0

    def test_fail(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_MOST, max_value=0.8)
        result = evaluate_metric("test", 0.95, goal)
        assert not result.passed
        assert result.distance == pytest.approx(0.15)

    def test_boundary(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_MOST, max_value=0.8)
        result = evaluate_metric("test", 0.8, goal)
        assert result.passed

    def test_missing_max_value_raises(self) -> None:
        with pytest.raises(VerificationError, match="max_value"):
            MetricGoal(type=MetricGoalType.AT_MOST)


# ---------------------------------------------------------------------------
# TARGET_BAND
# ---------------------------------------------------------------------------


class TestTargetBand:
    def test_pass(self) -> None:
        goal = MetricGoal(type=MetricGoalType.TARGET_BAND, target=0.7, tolerance=0.1)
        result = evaluate_metric("test", 0.72, goal)
        assert result.passed

    def test_fail(self) -> None:
        goal = MetricGoal(type=MetricGoalType.TARGET_BAND, target=0.7, tolerance=0.1)
        result = evaluate_metric("test", 0.5, goal)
        assert not result.passed
        assert result.distance == pytest.approx(0.1)

    def test_boundary(self) -> None:
        goal = MetricGoal(type=MetricGoalType.TARGET_BAND, target=0.7, tolerance=0.1)
        result = evaluate_metric("test", 0.8, goal)
        assert result.passed

    def test_missing_target_raises(self) -> None:
        with pytest.raises(VerificationError, match="target"):
            MetricGoal(type=MetricGoalType.TARGET_BAND, tolerance=0.1)


# ---------------------------------------------------------------------------
# BETWEEN
# ---------------------------------------------------------------------------


class TestBetween:
    def test_pass(self) -> None:
        goal = MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=0.8)
        result = evaluate_metric("test", 0.5, goal)
        assert result.passed

    def test_fail_below(self) -> None:
        goal = MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=0.8)
        result = evaluate_metric("test", 0.1, goal)
        assert not result.passed
        assert result.distance == pytest.approx(0.2)

    def test_fail_above(self) -> None:
        goal = MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=0.8)
        result = evaluate_metric("test", 0.95, goal)
        assert not result.passed
        assert result.distance == pytest.approx(0.15)

    def test_boundary_low(self) -> None:
        goal = MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=0.8)
        result = evaluate_metric("test", 0.3, goal)
        assert result.passed

    def test_boundary_high(self) -> None:
        goal = MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3, max_value=0.8)
        result = evaluate_metric("test", 0.8, goal)
        assert result.passed

    def test_missing_fields_raises(self) -> None:
        with pytest.raises(VerificationError, match="min_value and max_value"):
            MetricGoal(type=MetricGoalType.BETWEEN, min_value=0.3)


# ---------------------------------------------------------------------------
# MATCH_CURVE
# ---------------------------------------------------------------------------


class TestMatchCurve:
    def test_pass_exact(self) -> None:
        curve = ((0.0, 0.2), (10.0, 0.8))
        goal = MetricGoal(
            type=MetricGoalType.MATCH_CURVE,
            target_curve=curve,
            tolerance=0.05,
        )
        # Actual values exactly on the curve
        actual = [(0.0, 0.2), (5.0, 0.5), (10.0, 0.8)]
        result = evaluate_metric("test", actual, goal)
        assert result.passed

    def test_fail_deviation(self) -> None:
        curve = ((0.0, 0.2), (10.0, 0.8))
        goal = MetricGoal(
            type=MetricGoalType.MATCH_CURVE,
            target_curve=curve,
            tolerance=0.05,
        )
        # Actual values far off the curve
        actual = [(0.0, 0.9), (5.0, 0.1), (10.0, 0.2)]
        result = evaluate_metric("test", actual, goal)
        assert not result.passed
        assert result.distance > 0

    def test_boundary_tolerance(self) -> None:
        curve = ((0.0, 0.5), (10.0, 0.5))
        goal = MetricGoal(
            type=MetricGoalType.MATCH_CURVE,
            target_curve=curve,
            tolerance=0.1,
        )
        actual = [(0.0, 0.6), (5.0, 0.4), (10.0, 0.6)]
        result = evaluate_metric("test", actual, goal)
        assert result.passed  # MAE = 0.1, equals tolerance

    def test_empty_data(self) -> None:
        curve = ((0.0, 0.5),)
        goal = MetricGoal(
            type=MetricGoalType.MATCH_CURVE,
            target_curve=curve,
            tolerance=0.1,
        )
        result = evaluate_metric("test", [], goal)
        assert not result.passed

    def test_missing_curve_raises(self) -> None:
        with pytest.raises(VerificationError, match="target_curve"):
            MetricGoal(type=MetricGoalType.MATCH_CURVE)


# ---------------------------------------------------------------------------
# RELATIVE_ORDER
# ---------------------------------------------------------------------------


class TestRelativeOrder:
    def test_pass(self) -> None:
        goal = MetricGoal(
            type=MetricGoalType.RELATIVE_ORDER,
            expected_order=("intro", "verse", "chorus"),
        )
        items = [("intro", 0.2), ("verse", 0.5), ("chorus", 0.9)]
        result = evaluate_metric("test", items, goal)
        assert result.passed

    def test_fail(self) -> None:
        goal = MetricGoal(
            type=MetricGoalType.RELATIVE_ORDER,
            expected_order=("intro", "verse", "chorus"),
        )
        items = [("intro", 0.9), ("verse", 0.5), ("chorus", 0.2)]
        result = evaluate_metric("test", items, goal)
        assert not result.passed

    def test_partial_items(self) -> None:
        goal = MetricGoal(
            type=MetricGoalType.RELATIVE_ORDER,
            expected_order=("intro", "verse", "chorus"),
        )
        # Only intro and chorus present, in correct order
        items = [("intro", 0.2), ("chorus", 0.9)]
        result = evaluate_metric("test", items, goal)
        assert result.passed

    def test_single_item_passes(self) -> None:
        goal = MetricGoal(
            type=MetricGoalType.RELATIVE_ORDER,
            expected_order=("intro", "verse"),
        )
        items = [("intro", 0.5)]
        result = evaluate_metric("test", items, goal)
        assert result.passed  # fewer than 2 comparable

    def test_missing_order_raises(self) -> None:
        with pytest.raises(VerificationError, match="expected_order"):
            MetricGoal(type=MetricGoalType.RELATIVE_ORDER)


# ---------------------------------------------------------------------------
# DIVERSITY
# ---------------------------------------------------------------------------


class TestDiversity:
    def test_pass(self) -> None:
        goal = MetricGoal(type=MetricGoalType.DIVERSITY, min_variance=0.01)
        values = [0.1, 0.5, 0.9, 0.3, 0.7]
        result = evaluate_metric("test", values, goal)
        assert result.passed

    def test_fail(self) -> None:
        goal = MetricGoal(type=MetricGoalType.DIVERSITY, min_variance=0.1)
        values = [0.5, 0.5, 0.5, 0.5]
        result = evaluate_metric("test", values, goal)
        assert not result.passed

    def test_boundary(self) -> None:
        # variance of [0, 1] = 0.25
        goal = MetricGoal(type=MetricGoalType.DIVERSITY, min_variance=0.25)
        values = [0.0, 1.0]
        result = evaluate_metric("test", values, goal)
        assert result.passed

    def test_single_value_fails(self) -> None:
        goal = MetricGoal(type=MetricGoalType.DIVERSITY, min_variance=0.01)
        result = evaluate_metric("test", [0.5], goal)
        assert not result.passed

    def test_missing_min_variance_raises(self) -> None:
        with pytest.raises(VerificationError, match="min_variance"):
            MetricGoal(type=MetricGoalType.DIVERSITY)


# ---------------------------------------------------------------------------
# MetricEvaluation structure
# ---------------------------------------------------------------------------


class TestMetricEvaluation:
    def test_has_required_fields(self) -> None:
        goal = MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.5)
        result = evaluate_metric("test_metric", 0.7, goal)
        assert isinstance(result, MetricEvaluation)
        assert result.metric_name == "test_metric"
        assert result.actual_value == 0.7
        assert result.goal is goal
        assert isinstance(result.explanation, str)
