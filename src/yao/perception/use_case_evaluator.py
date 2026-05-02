"""Use-Case Targeted Evaluators — evaluate against intended purpose.

Each ``UseCase`` has exactly one evaluator class that scores a
``PerceptualReport`` against use-case-specific criteria.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from yao.errors import YaOError
from yao.perception.audio_features import PerceptualReport
from yao.schema.intent import IntentSpec


class EvaluatorError(YaOError):
    """Raised when an evaluator produces an invalid score."""


class UseCase(Enum):
    """Supported use cases for targeted evaluation."""

    YOUTUBE_BGM = "youtube_bgm"
    GAME_BGM = "game_bgm"
    ADVERTISEMENT = "advertisement"
    STUDY_FOCUS = "study_focus"
    MEDITATION = "meditation"
    WORKOUT = "workout"
    CINEMATIC = "cinematic"


class UseCaseRules(ABC):
    """Abstract base for use-case-specific evaluation rules.

    Each subclass defines score keys and computes scores in [0.0, 1.0].
    """

    @abstractmethod
    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate a PerceptualReport against use-case criteria.

        Args:
            report: Audio analysis report.
            intent: The composition's intent spec.

        Returns:
            Dict of score_key → float in [0.0, 1.0].
        """
        ...


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _clamp01(value: float) -> float:
    """Clamp a value to [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def _lufs_proximity(actual: float, target: float, tolerance: float = 3.0) -> float:
    """Score how close actual LUFS is to target (1.0 = exact match)."""
    diff = abs(actual - target)
    return _clamp01(1.0 - diff / tolerance)


def _dynamic_range_score(dr_db: float, ideal_low: float, ideal_high: float) -> float:
    """Score dynamic range fitness (1.0 = within ideal range)."""
    if ideal_low <= dr_db <= ideal_high:
        return 1.0
    if dr_db < ideal_low:
        return _clamp01(dr_db / ideal_low)
    return _clamp01(ideal_high / dr_db)


# ---------------------------------------------------------------------------
# Concrete evaluators
# ---------------------------------------------------------------------------


class YouTubeBGMRules(UseCaseRules):
    """YouTube background music: vocal space, loopability, fatigue risk."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for YouTube BGM suitability."""
        from yao.perception.audio_features import BandName

        # Vocal space: mid frequencies should leave room (lower energy = better)
        mid_energy = report.frequency_band_energy.get(BandName.MID, 0.5)
        vocal_space = _clamp01(1.0 - mid_energy * 1.5)

        # Loopability: low dynamic range → easier to loop
        loopability = _clamp01(1.0 - report.dynamic_range_db / 20.0)

        # Fatigue risk: low spectral flatness → less fatiguing
        fatigue_risk = _clamp01(1.0 - report.spectral_flatness * 2.0)

        # LUFS target: YouTube typically -14 LUFS
        lufs_match = _lufs_proximity(report.lufs_integrated, -14.0)

        return {
            "vocal_space_score": vocal_space,
            "loopability": loopability,
            "fatigue_risk": fatigue_risk,
            "lufs_target_match": lufs_match,
        }


class GameBGMRules(UseCaseRules):
    """Game background music: loop seam, tension curve, repetition tolerance."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for game BGM suitability."""
        # Loop seam: low dynamic range at boundaries → smoother loop
        loop_seam = _clamp01(1.0 - report.dynamic_range_db / 15.0)

        # Tension curve: consistent onset density across sections
        densities = list(report.onset_density_per_section.values())
        if len(densities) >= 2:
            density_range = max(densities) - min(densities)
            tension_match = _clamp01(1.0 - density_range / 5.0)
        else:
            tension_match = 0.7

        # Repetition tolerance: higher spectral flatness → more drone-like → tolerable
        repetition = _clamp01(report.spectral_flatness * 2.0 + 0.3)

        return {
            "loop_seam_smoothness": loop_seam,
            "tension_curve_match": tension_match,
            "repetition_tolerance": repetition,
        }


class AdvertisementRules(UseCaseRules):
    """Advertisement music: hook timing, peak position, memorability."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for advertisement suitability."""
        # Hook entry time: first onset should be within 7 seconds
        first_onset = 0.0
        for section_density in report.onset_density_per_section.values():
            if section_density > 0:
                first_onset = 1.0
                break
        hook_entry = _clamp01(first_onset)

        # Peak position: loudest moment in first half → good for ads
        st_values = [v for _, v in report.lufs_short_term if v > -70]
        if len(st_values) >= 3:
            peak_idx = st_values.index(max(st_values))
            peak_pos = _clamp01(1.0 - peak_idx / len(st_values))
        else:
            peak_pos = 0.5

        # Memorability: moderate onset density + low masking
        avg_density = sum(report.onset_density_per_section.values()) / max(len(report.onset_density_per_section), 1)
        memo = _clamp01(avg_density / 5.0) * _clamp01(1.0 - report.masking_risk_score)

        return {
            "hook_entry_time": hook_entry,
            "peak_position": peak_pos,
            "short_form_memorability": memo,
        }


class StudyFocusRules(UseCaseRules):
    """Study/focus music: low distraction, stability, predictability."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for study/focus suitability."""
        # Low distraction: low onset density
        avg_density = sum(report.onset_density_per_section.values()) / max(len(report.onset_density_per_section), 1)
        low_distraction = _clamp01(1.0 - avg_density / 8.0)

        # Dynamic stability: low dynamic range
        stability = _clamp01(1.0 - report.dynamic_range_db / 10.0)

        # Predictability: low tempo drift → predictable
        predictability = _clamp01(1.0 - report.tempo_stability_ms_drift / 50.0)

        return {
            "low_distraction_score": low_distraction,
            "dynamic_stability": stability,
            "predictability": predictability,
        }


class MeditationRules(UseCaseRules):
    """Meditation music: gentle dynamics, slow tempo, low surprise."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for meditation suitability."""
        # Gentle dynamics: very low dynamic range
        gentle = _clamp01(1.0 - report.dynamic_range_db / 6.0)

        # Slow tempo consistency: low tempo drift
        tempo_cons = _clamp01(1.0 - report.tempo_stability_ms_drift / 30.0)

        # Low surprise: low onset density + low spectral variation
        avg_density = sum(report.onset_density_per_section.values()) / max(len(report.onset_density_per_section), 1)
        low_surprise = _clamp01(1.0 - avg_density / 4.0)

        return {
            "gentle_dynamics": gentle,
            "slow_tempo_consistency": tempo_cons,
            "low_surprise": low_surprise,
        }


class WorkoutRules(UseCaseRules):
    """Workout music: tempo consistency, energy, motivational arc."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for workout suitability."""
        # Tempo consistency: low drift
        tempo_cons = _clamp01(1.0 - report.tempo_stability_ms_drift / 40.0)

        # Energy consistency: high onset density across sections
        densities = list(report.onset_density_per_section.values())
        avg_density = sum(densities) / max(len(densities), 1)
        energy = _clamp01(avg_density / 6.0)

        # Motivational arc: dynamic range should exist but not be extreme
        arc = _dynamic_range_score(report.dynamic_range_db, 3.0, 12.0)

        return {
            "tempo_consistency": tempo_cons,
            "energy_consistency": energy,
            "motivational_arc": arc,
        }


class CinematicScoreRules(UseCaseRules):
    """Cinematic score: arc clarity, climax position, emotional coherence."""

    def evaluate(self, report: PerceptualReport, intent: IntentSpec) -> dict[str, float]:
        """Evaluate for cinematic score suitability."""
        # Arc clarity: significant dynamic range → clear arc
        arc = _dynamic_range_score(report.dynamic_range_db, 6.0, 20.0)

        # Climax position: loudest moment in latter half (2/3 mark ideal)
        st_values = [v for _, v in report.lufs_short_term if v > -70]
        if len(st_values) >= 3:
            peak_idx = st_values.index(max(st_values))
            # Ideal at 2/3 point
            ideal_pos = len(st_values) * 2 / 3
            climax_pos = _clamp01(1.0 - abs(peak_idx - ideal_pos) / len(st_values))
        else:
            climax_pos = 0.5

        # Emotional coherence: low masking + moderate spectral variation
        coherence = _clamp01(1.0 - report.masking_risk_score)

        return {
            "arc_clarity": arc,
            "climax_position": climax_pos,
            "emotional_coherence": coherence,
        }


# ---------------------------------------------------------------------------
# Registry and evaluator entry point
# ---------------------------------------------------------------------------

_USE_CASE_EVALUATORS: dict[UseCase, type[UseCaseRules]] = {
    UseCase.YOUTUBE_BGM: YouTubeBGMRules,
    UseCase.GAME_BGM: GameBGMRules,
    UseCase.ADVERTISEMENT: AdvertisementRules,
    UseCase.STUDY_FOCUS: StudyFocusRules,
    UseCase.MEDITATION: MeditationRules,
    UseCase.WORKOUT: WorkoutRules,
    UseCase.CINEMATIC: CinematicScoreRules,
}


class UseCaseEvaluator:
    """Evaluates a PerceptualReport against a specific use case.

    Usage::

        evaluator = UseCaseEvaluator()
        scores = evaluator.evaluate(report, intent, UseCase.YOUTUBE_BGM)
    """

    def evaluate(
        self,
        report: PerceptualReport,
        intent: IntentSpec,
        use_case: UseCase,
    ) -> dict[str, float]:
        """Run use-case-specific evaluation.

        Args:
            report: Audio perception analysis report.
            intent: The composition's intent.
            use_case: The target use case.

        Returns:
            Dict of score_key → float, all in [0.0, 1.0].

        Raises:
            EvaluatorError: If a score falls outside [0.0, 1.0].
        """
        rules_cls = _USE_CASE_EVALUATORS.get(use_case)
        if rules_cls is None:
            available = [uc.value for uc in UseCase]
            raise EvaluatorError(f"Unknown use case '{use_case}'. Available: {available}")

        rules = rules_cls()
        scores = rules.evaluate(report, intent)

        # Validate all scores are in [0.0, 1.0]
        for key, value in scores.items():
            if not 0.0 <= value <= 1.0:
                raise EvaluatorError(f"Score '{key}' = {value} is outside [0.0, 1.0] for use case {use_case.value}.")

        return scores
