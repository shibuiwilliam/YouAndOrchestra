"""Tests for dynamic evaluation weights via GenreProfile."""

from __future__ import annotations

from yao.schema.genre_profile import GenreEvaluationSection, UnifiedGenreProfile
from yao.verify.evaluator import EvaluationReport, EvaluationScore


class TestDynamicWeights:
    """Test that GenreProfile-driven weights change quality_score."""

    def _make_report(
        self,
        weights: dict[str, float] | None = None,
    ) -> EvaluationReport:
        """Build a report with fixed scores across dimensions."""
        report = EvaluationReport(title="Test", dimension_weights=weights)
        # Structure: high score
        report.scores.append(
            EvaluationScore(
                dimension="structure",
                metric="test_struct",
                score=0.9,
                target=0.5,
                tolerance=0.5,
                detail="high",
            )
        )
        # Melody: low score
        report.scores.append(
            EvaluationScore(
                dimension="melody",
                metric="test_melody",
                score=0.3,
                target=0.5,
                tolerance=0.5,
                detail="low",
            )
        )
        # Harmony: medium score
        report.scores.append(
            EvaluationScore(
                dimension="harmony",
                metric="test_harmony",
                score=0.6,
                target=0.5,
                tolerance=0.5,
                detail="medium",
            )
        )
        return report

    def test_default_weights_produce_baseline(self) -> None:
        report = self._make_report()
        baseline = report.quality_score
        assert 1.0 <= baseline <= 10.0

    def test_custom_weights_change_score(self) -> None:
        # Default weights
        report_default = self._make_report()
        # Custom weights: heavily favor structure (which scores 0.9)
        report_custom = self._make_report(weights={"structure": 0.8, "melody": 0.1, "harmony": 0.1})
        # The structure-favoring weights should produce a higher score
        # since structure has the highest score (0.9)
        assert report_custom.quality_score > report_default.quality_score

    def test_melody_heavy_weights_lower_score(self) -> None:
        report_default = self._make_report()
        # Melody scores low (0.3), so weighting it heavily should lower score
        report_melody = self._make_report(weights={"structure": 0.1, "melody": 0.8, "harmony": 0.1})
        assert report_melody.quality_score < report_default.quality_score

    def test_none_weights_use_defaults(self) -> None:
        report = self._make_report(weights=None)
        # Should use _DIMENSION_WEIGHTS — verify it's not crashing
        assert 1.0 <= report.quality_score <= 10.0

    def test_empty_weights_still_works(self) -> None:
        report = self._make_report(weights={})
        # Empty dict means no dimensions have weight — should return 5.0 (default)
        assert report.quality_score == 5.0


class TestPercussionCentric:
    """Test percussion_centric flag in GenreProfile."""

    def test_percussion_centric_profile(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="techno",
            evaluation=GenreEvaluationSection(
                weights={"structure": 0.3, "arrangement": 0.3},
                percussion_centric=True,
            ),
        )
        assert profile.evaluation.percussion_centric is True

    def test_non_percussion_centric_default(self) -> None:
        profile = UnifiedGenreProfile(genre_id="jazz")
        assert profile.evaluation.percussion_centric is False


class TestEvaluateScoreWithProfile:
    """Test evaluate_score() with genre_profile parameter."""

    def test_evaluate_score_accepts_genre_profile(self) -> None:
        """Verify the function signature accepts genre_profile without error."""
        # Just check the signature accepts the parameter
        import inspect

        from yao.verify.evaluator import evaluate_score

        sig = inspect.signature(evaluate_score)
        assert "genre_profile" in sig.parameters
