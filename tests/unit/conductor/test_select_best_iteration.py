"""P0.2: the conductor must keep the BEST iteration, not the last one."""

from __future__ import annotations

from yao.conductor.conductor import select_best_iteration
from yao.verify.evaluator import EvaluationReport, EvaluationScore


def _report(passes: int, total: int, avg_score: float) -> EvaluationReport:
    """Build a report with `passes` passing of `total` melody metrics."""
    scores = []
    for i in range(total):
        passed = i < passes
        scores.append(
            EvaluationScore(
                dimension="melody",
                metric=f"m{i}",
                score=avg_score,
                target=avg_score,
                tolerance=0.0,
                detail="",
                goal_passed=passed,
            )
        )
    return EvaluationReport(title="t", scores=scores)


def _snap(iteration: int, passes: int, total: int, avg: float) -> dict[str, object]:
    return {"iteration": iteration, "evaluation": _report(passes, total, avg)}


def test_empty_returns_none() -> None:
    assert select_best_iteration([]) is None


def test_picks_higher_pass_rate_even_if_not_last() -> None:
    snaps = [
        _snap(1, passes=4, total=4, avg=0.8),  # 100% pass
        _snap(2, passes=1, total=4, avg=0.9),  # 25% pass — a regression
    ]
    best = select_best_iteration(snaps)
    assert best is not None
    assert best["iteration"] == 1  # NOT the last iteration


def test_quality_breaks_ties_on_equal_pass_rate() -> None:
    snaps = [
        _snap(1, passes=2, total=4, avg=0.5),
        _snap(2, passes=2, total=4, avg=0.9),  # same pass rate, higher quality
        _snap(3, passes=2, total=4, avg=0.6),
    ]
    best = select_best_iteration(snaps)
    assert best is not None
    assert best["iteration"] == 2


def test_last_iteration_wins_when_it_is_actually_best() -> None:
    snaps = [
        _snap(1, passes=1, total=4, avg=0.5),
        _snap(2, passes=2, total=4, avg=0.6),
        _snap(3, passes=4, total=4, avg=0.8),
    ]
    best = select_best_iteration(snaps)
    assert best is not None
    assert best["iteration"] == 3
