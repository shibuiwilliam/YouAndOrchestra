"""Tests for Use-Case Targeted Evaluators."""

from __future__ import annotations

import pytest

from yao.perception.audio_features import BandName, PerceptualReport
from yao.perception.use_case_evaluator import (
    UseCase,
    UseCaseEvaluator,
)
from yao.schema.intent import IntentSpec


def _make_report(
    *,
    lufs: float = -14.0,
    dynamic_range: float = 6.0,
    onset_density: float = 3.0,
    tempo_drift: float = 10.0,
    flatness: float = 0.1,
    masking: float = 0.2,
) -> PerceptualReport:
    """Create a minimal PerceptualReport for testing."""
    return PerceptualReport(
        lufs_integrated=lufs,
        lufs_short_term=((0.0, lufs), (3.0, lufs + 1), (6.0, lufs - 1)),
        peak_dbfs=-1.0,
        dynamic_range_db=dynamic_range,
        spectral_centroid_mean=2000.0,
        spectral_centroid_per_section={"full": 2000.0},
        spectral_rolloff=8000.0,
        spectral_flatness=flatness,
        onset_density_per_section={"full": onset_density},
        tempo_stability_ms_drift=tempo_drift,
        frequency_band_energy={
            BandName.SUB_BASS: 0.05,
            BandName.BASS: 0.15,
            BandName.LOW_MID: 0.20,
            BandName.MID: 0.25,
            BandName.HIGH_MID: 0.15,
            BandName.PRESENCE: 0.10,
            BandName.BRILLIANCE: 0.10,
        },
        masking_risk_score=masking,
    )


def _make_intent(use_case: str | None = None) -> IntentSpec:
    return IntentSpec(text="Test intent", keywords=["test"], use_case_hint=use_case)


class TestAllUseCasesReturnValidScores:
    """Every evaluator must return scores in [0.0, 1.0]."""

    @pytest.mark.parametrize("use_case", list(UseCase))
    def test_scores_in_range(self, use_case: UseCase) -> None:
        evaluator = UseCaseEvaluator()
        report = _make_report()
        intent = _make_intent()
        scores = evaluator.evaluate(report, intent, use_case)
        assert isinstance(scores, dict)
        assert len(scores) > 0
        for key, value in scores.items():
            assert 0.0 <= value <= 1.0, f"{use_case.value}.{key} = {value}"


class TestEachUseCaseHasUniqueEvaluator:
    def test_seven_use_cases(self) -> None:
        assert len(UseCase) == 7  # noqa: PLR2004

    @pytest.mark.parametrize("use_case", list(UseCase))
    def test_evaluator_exists(self, use_case: UseCase) -> None:
        evaluator = UseCaseEvaluator()
        scores = evaluator.evaluate(_make_report(), _make_intent(), use_case)
        assert len(scores) >= 2  # noqa: PLR2004


class TestYouTubeBGM:
    def test_good_youtube_bgm(self) -> None:
        # Quiet, low dynamic range, low mid energy = good BGM
        report = _make_report(lufs=-14.0, dynamic_range=3.0, flatness=0.05)
        scores = UseCaseEvaluator().evaluate(report, _make_intent(), UseCase.YOUTUBE_BGM)
        assert scores["lufs_target_match"] > 0.5
        assert scores["loopability"] > 0.5

    def test_bad_youtube_bgm(self) -> None:
        # Very loud, high dynamic range = bad BGM
        report = _make_report(lufs=-5.0, dynamic_range=15.0)
        scores = UseCaseEvaluator().evaluate(report, _make_intent(), UseCase.YOUTUBE_BGM)
        assert scores["lufs_target_match"] < 0.5


class TestStudyFocus:
    def test_calm_is_good_for_study(self) -> None:
        report = _make_report(onset_density=1.0, dynamic_range=2.0, tempo_drift=5.0)
        scores = UseCaseEvaluator().evaluate(report, _make_intent(), UseCase.STUDY_FOCUS)
        assert scores["low_distraction_score"] > 0.5
        assert scores["dynamic_stability"] > 0.5

    def test_busy_is_bad_for_study(self) -> None:
        report = _make_report(onset_density=8.0, dynamic_range=12.0)
        scores = UseCaseEvaluator().evaluate(report, _make_intent(), UseCase.STUDY_FOCUS)
        assert scores["low_distraction_score"] < 0.5


class TestWorkout:
    def test_energetic_is_good(self) -> None:
        report = _make_report(onset_density=5.0, tempo_drift=5.0, dynamic_range=6.0)
        scores = UseCaseEvaluator().evaluate(report, _make_intent(), UseCase.WORKOUT)
        assert scores["energy_consistency"] > 0.5
        assert scores["tempo_consistency"] > 0.5


class TestCinematic:
    def test_wide_arc_is_good(self) -> None:
        report = _make_report(dynamic_range=10.0, masking=0.1)
        scores = UseCaseEvaluator().evaluate(report, _make_intent(), UseCase.CINEMATIC)
        assert scores["arc_clarity"] > 0.5
        assert scores["emotional_coherence"] > 0.5


class TestErrorHandling:
    def test_scores_always_clamped(self) -> None:
        # Extreme values should still produce [0, 1] scores
        report = _make_report(lufs=-50.0, dynamic_range=50.0, onset_density=100.0)
        evaluator = UseCaseEvaluator()
        for use_case in UseCase:
            scores = evaluator.evaluate(report, _make_intent(), use_case)
            for key, value in scores.items():
                assert 0.0 <= value <= 1.0, f"Extreme: {use_case.value}.{key} = {value}"
