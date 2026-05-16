"""A/B Testing Framework — structured hypothesis validation for generation.

Runs multiple seeds under different configurations, collects metrics,
and determines which variant performs better. Supports both automated
(evaluation score) and human-in-the-loop (rating) assessment.

Belongs to Layer 7 (Reflection).
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Hypothesis:
    """A testable hypothesis about generation quality.

    Attributes:
        name: Short identifier (e.g., "swing_improves_jazz_feel").
        description: What we're testing.
        metric: Evaluation metric to measure (e.g., "groove_pocket", "overall").
        direction: "higher" if higher metric = better, "lower" if lower = better.
    """

    name: str
    description: str
    metric: str
    direction: str = "higher"


@dataclass(frozen=True)
class Variant:
    """One arm of an A/B test.

    Attributes:
        name: Variant identifier (e.g., "control", "treatment").
        overrides: Spec overrides applied to the base composition.
    """

    name: str
    overrides: dict[str, Any] = field(default_factory=dict)


@dataclass
class VariantResult:
    """Collected results for a single variant.

    Attributes:
        variant: The variant configuration.
        scores: Metric scores from each seed run.
        seeds_used: Random seeds used for generation.
    """

    variant: Variant
    scores: list[float] = field(default_factory=list)
    seeds_used: list[int] = field(default_factory=list)

    @property
    def mean(self) -> float:
        """Mean score across all runs."""
        return statistics.mean(self.scores) if self.scores else 0.0

    @property
    def stdev(self) -> float:
        """Standard deviation of scores."""
        if len(self.scores) < 2:  # noqa: PLR2004
            return 0.0
        return statistics.stdev(self.scores)

    @property
    def n(self) -> int:
        """Number of runs."""
        return len(self.scores)


@dataclass(frozen=True)
class ABTestResult:
    """Result of an A/B test comparison.

    Attributes:
        hypothesis: The hypothesis tested.
        variant_a: Results for variant A (control).
        variant_b: Results for variant B (treatment).
        winner: Name of the winning variant, or "inconclusive".
        effect_size: Cohen's d effect size (positive = B better if direction=higher).
        confidence: Rough confidence level based on sample overlap.
    """

    hypothesis: Hypothesis
    variant_a: VariantResult
    variant_b: VariantResult
    winner: str
    effect_size: float
    confidence: float


def compute_effect_size(a_scores: list[float], b_scores: list[float]) -> float:
    """Compute Cohen's d effect size between two groups.

    Args:
        a_scores: Scores from variant A.
        b_scores: Scores from variant B.

    Returns:
        Cohen's d (positive = B higher than A).
    """
    if len(a_scores) < 2 or len(b_scores) < 2:  # noqa: PLR2004
        return 0.0
    mean_a = statistics.mean(a_scores)
    mean_b = statistics.mean(b_scores)
    var_a = statistics.variance(a_scores)
    var_b = statistics.variance(b_scores)
    pooled_std = ((var_a + var_b) / 2.0) ** 0.5
    if pooled_std == 0:
        return 0.0
    return float((mean_b - mean_a) / pooled_std)


def run_ab_test(
    hypothesis: Hypothesis,
    variant_a: VariantResult,
    variant_b: VariantResult,
) -> ABTestResult:
    """Evaluate an A/B test given collected results.

    Args:
        hypothesis: The hypothesis being tested.
        variant_a: Collected results for control.
        variant_b: Collected results for treatment.

    Returns:
        ABTestResult with winner determination and effect size.
    """
    effect = compute_effect_size(variant_a.scores, variant_b.scores)

    # Determine winner based on direction
    if hypothesis.direction == "lower":
        effect = -effect

    # Heuristic confidence based on effect size and sample count
    min_n = min(variant_a.n, variant_b.n)
    if min_n < 3:  # noqa: PLR2004
        confidence = 0.0
        winner = "inconclusive"
    elif abs(effect) < 0.2:  # noqa: PLR2004
        confidence = min(0.5, min_n / 20.0)
        winner = "inconclusive"
    elif abs(effect) < 0.5:  # noqa: PLR2004
        confidence = min(0.7, min_n / 10.0)
        winner = variant_b.variant.name if effect > 0 else variant_a.variant.name
    else:
        confidence = min(0.95, min_n / 8.0)
        winner = variant_b.variant.name if effect > 0 else variant_a.variant.name

    return ABTestResult(
        hypothesis=hypothesis,
        variant_a=variant_a,
        variant_b=variant_b,
        winner=winner,
        effect_size=round(effect, 4),
        confidence=round(confidence, 3),
    )


def save_ab_result(result: ABTestResult, path: Path) -> None:
    """Save an A/B test result to JSON.

    Args:
        result: The test result.
        path: Output path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "hypothesis": {
            "name": result.hypothesis.name,
            "description": result.hypothesis.description,
            "metric": result.hypothesis.metric,
            "direction": result.hypothesis.direction,
        },
        "variant_a": {
            "name": result.variant_a.variant.name,
            "overrides": result.variant_a.variant.overrides,
            "scores": result.variant_a.scores,
            "seeds": result.variant_a.seeds_used,
            "mean": result.variant_a.mean,
            "stdev": result.variant_a.stdev,
            "n": result.variant_a.n,
        },
        "variant_b": {
            "name": result.variant_b.variant.name,
            "overrides": result.variant_b.variant.overrides,
            "scores": result.variant_b.scores,
            "seeds": result.variant_b.seeds_used,
            "mean": result.variant_b.mean,
            "stdev": result.variant_b.stdev,
            "n": result.variant_b.n,
        },
        "winner": result.winner,
        "effect_size": result.effect_size,
        "confidence": result.confidence,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
