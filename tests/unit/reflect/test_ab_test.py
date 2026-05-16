"""Tests for the A/B testing framework."""

from __future__ import annotations

from pathlib import Path

from yao.reflect.ab_test import (
    Hypothesis,
    Variant,
    VariantResult,
    compute_effect_size,
    run_ab_test,
    save_ab_result,
)


class TestComputeEffectSize:
    """Tests for Cohen's d effect size computation."""

    def test_identical_groups_zero_effect(self) -> None:
        """Identical groups should have zero effect size."""
        scores = [0.5, 0.6, 0.7, 0.5, 0.6]
        assert compute_effect_size(scores, scores) == 0.0

    def test_clearly_different_groups(self) -> None:
        """Clearly different groups should have large effect size."""
        a = [0.3, 0.35, 0.32, 0.28, 0.31]
        b = [0.7, 0.75, 0.72, 0.68, 0.71]
        effect = compute_effect_size(a, b)
        assert effect > 1.0  # Large effect

    def test_positive_when_b_higher(self) -> None:
        """Effect should be positive when B scores higher than A."""
        a = [0.4, 0.45, 0.42]
        b = [0.6, 0.65, 0.62]
        assert compute_effect_size(a, b) > 0

    def test_negative_when_a_higher(self) -> None:
        """Effect should be negative when A scores higher than B."""
        a = [0.7, 0.75, 0.72]
        b = [0.3, 0.35, 0.32]
        assert compute_effect_size(a, b) < 0

    def test_insufficient_samples_returns_zero(self) -> None:
        """With fewer than 2 samples, effect size should be 0."""
        assert compute_effect_size([0.5], [0.6]) == 0.0
        assert compute_effect_size([], []) == 0.0


class TestVariantResult:
    """Tests for VariantResult statistics."""

    def test_mean_calculation(self) -> None:
        """Mean should be correctly computed."""
        vr = VariantResult(variant=Variant(name="test"))
        vr.scores = [0.4, 0.6, 0.8]
        assert abs(vr.mean - 0.6) < 0.001

    def test_empty_mean_is_zero(self) -> None:
        """Empty scores should have mean 0."""
        vr = VariantResult(variant=Variant(name="test"))
        assert vr.mean == 0.0

    def test_stdev_single_sample(self) -> None:
        """Single sample should have stdev 0."""
        vr = VariantResult(variant=Variant(name="test"))
        vr.scores = [0.5]
        assert vr.stdev == 0.0

    def test_n_matches_scores_length(self) -> None:
        """N should match number of scores."""
        vr = VariantResult(variant=Variant(name="test"))
        vr.scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        assert vr.n == 5


class TestRunABTest:
    """Tests for the full A/B test evaluation."""

    def test_clear_winner_detected(self) -> None:
        """A clear difference should produce a winner."""
        hypothesis = Hypothesis(name="test", description="Test hypothesis", metric="overall")
        va = VariantResult(variant=Variant(name="control"))
        va.scores = [0.3, 0.32, 0.28, 0.31, 0.29]
        vb = VariantResult(variant=Variant(name="treatment"))
        vb.scores = [0.7, 0.72, 0.68, 0.71, 0.69]

        result = run_ab_test(hypothesis, va, vb)
        assert result.winner == "treatment"
        assert result.effect_size > 0
        assert result.confidence > 0

    def test_inconclusive_with_similar_scores(self) -> None:
        """Very similar scores should be inconclusive."""
        hypothesis = Hypothesis(name="test", description="Test", metric="overall")
        va = VariantResult(variant=Variant(name="A"))
        va.scores = [0.500, 0.501, 0.499, 0.500, 0.502]
        vb = VariantResult(variant=Variant(name="B"))
        vb.scores = [0.501, 0.500, 0.499, 0.501, 0.500]

        result = run_ab_test(hypothesis, va, vb)
        assert result.winner == "inconclusive"

    def test_too_few_samples_inconclusive(self) -> None:
        """With < 3 samples, result should be inconclusive."""
        hypothesis = Hypothesis(name="test", description="Test", metric="overall")
        va = VariantResult(variant=Variant(name="A"))
        va.scores = [0.3, 0.4]
        vb = VariantResult(variant=Variant(name="B"))
        vb.scores = [0.7, 0.8]

        result = run_ab_test(hypothesis, va, vb)
        assert result.winner == "inconclusive"

    def test_lower_direction_inverts(self) -> None:
        """With direction='lower', lower scores should win."""
        hypothesis = Hypothesis(
            name="test",
            description="Test",
            metric="latency",
            direction="lower",
        )
        va = VariantResult(variant=Variant(name="control"))
        va.scores = [0.7, 0.72, 0.68, 0.71, 0.69]
        vb = VariantResult(variant=Variant(name="treatment"))
        vb.scores = [0.3, 0.32, 0.28, 0.31, 0.29]

        result = run_ab_test(hypothesis, va, vb)
        assert result.winner == "treatment"


class TestSaveABResult:
    """Tests for result persistence."""

    def test_save_and_read(self, tmp_path: Path) -> None:
        """Saved result should be valid JSON."""
        import json

        hypothesis = Hypothesis(name="test", description="Test", metric="overall")
        va = VariantResult(variant=Variant(name="A"))
        va.scores = [0.5, 0.6]
        vb = VariantResult(variant=Variant(name="B"))
        vb.scores = [0.7, 0.8]

        result = run_ab_test(hypothesis, va, vb)
        out = tmp_path / "result.json"
        save_ab_result(result, out)

        data = json.loads(out.read_text())
        assert data["hypothesis"]["name"] == "test"
        assert data["variant_a"]["name"] == "A"
        assert data["variant_b"]["name"] == "B"
        assert "winner" in data
        assert "effect_size" in data
