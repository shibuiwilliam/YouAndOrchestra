"""P2.1a: EvaluationScore.passed must honor the MetricGoal result.

Regression for the discarded ``result.passed`` in ``_score_via_goal``: the
legacy symmetric ``abs(score - target) <= tolerance`` check is wrong for
directional and non-scalar goals. EvaluationScore now carries the
authoritative ``goal_passed``.
"""

from __future__ import annotations

from yao.verify.evaluator import EvaluationScore, _score_via_goal
from yao.verify.metric_goal import MetricGoal, MetricGoalType


class TestGoalPassedOverride:
    def test_goal_passed_true_overrides_legacy_fail(self) -> None:
        """goal_passed=True wins even if the symmetric check would fail."""
        score = EvaluationScore(
            dimension="melody",
            metric="m",
            score=0.0,
            target=1.0,
            tolerance=0.1,  # legacy check: |0-1|=1 > 0.1 → would be False
            detail="",
            goal_passed=True,
        )
        assert score.passed is True

    def test_goal_passed_false_overrides_legacy_pass(self) -> None:
        """goal_passed=False wins even if the symmetric check would pass."""
        score = EvaluationScore(
            dimension="melody",
            metric="m",
            score=0.5,
            target=0.5,
            tolerance=0.1,  # legacy check: |0.5-0.5|=0 ≤ 0.1 → would be True
            detail="",
            goal_passed=False,
        )
        assert score.passed is False

    def test_none_preserves_legacy_behavior(self) -> None:
        """goal_passed=None falls back to the symmetric tolerance check."""
        passing = EvaluationScore("melody", "m", 0.52, 0.5, 0.1, "", goal_passed=None)
        failing = EvaluationScore("melody", "m", 0.9, 0.5, 0.1, "", goal_passed=None)
        assert passing.passed is True
        assert failing.passed is False


class TestScoreViaGoalCarriesResult:
    def test_at_least_below_threshold_fails(self) -> None:
        score = _score_via_goal("structure", "m", 0.30, MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.5))
        assert score.goal_passed is False
        assert score.passed is False

    def test_at_least_meets_threshold_passes(self) -> None:
        score = _score_via_goal("structure", "m", 0.80, MetricGoal(type=MetricGoalType.AT_LEAST, min_value=0.5))
        assert score.goal_passed is True
        assert score.passed is True

    def test_at_most_above_ceiling_fails(self) -> None:
        score = _score_via_goal("structure", "m", 0.70, MetricGoal(type=MetricGoalType.AT_MOST, max_value=0.6))
        assert score.goal_passed is False
        assert score.passed is False

    def test_diversity_goal_not_always_passing(self) -> None:
        """Non-scalar goals used to hit the else-branch and always pass.

        With goal_passed carried through, an insufficient-variance result
        genuinely fails.
        """
        score = _score_via_goal(
            "melody",
            "m",
            [0.5, 0.5, 0.5],  # zero variance
            MetricGoal(type=MetricGoalType.DIVERSITY, min_variance=0.1),
        )
        assert score.goal_passed is False
        assert score.passed is False
