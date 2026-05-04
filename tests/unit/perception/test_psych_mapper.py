"""Tests for PSL-Psychology: emotion-to-feature mapping.

Verifies that the empirical emotion → musical feature mapping is
internally consistent and provides useful generator parameters.
"""

from __future__ import annotations

import pytest

from yao.perception.psych_mapper import (
    EMOTION_TO_FEATURES,
    all_emotions,
    emotion_to_generator_params,
    get_feature_profile,
)


class TestFeatureProfileValues:
    """Verify all profiles have valid values."""

    @pytest.mark.parametrize("emotion", list(EMOTION_TO_FEATURES.keys()))
    def test_tempo_range_valid(self, emotion: str) -> None:
        """Tempo range should have min < max, both in reasonable bounds."""
        profile = EMOTION_TO_FEATURES[emotion]
        low, high = profile.tempo_bpm_range
        assert 30 <= low < high <= 200, f"{emotion}: tempo ({low}, {high}) invalid"

    @pytest.mark.parametrize("emotion", list(EMOTION_TO_FEATURES.keys()))
    def test_bias_in_range(self, emotion: str) -> None:
        """major_minor_bias should be in [0, 1]."""
        profile = EMOTION_TO_FEATURES[emotion]
        assert 0.0 <= profile.major_minor_bias <= 1.0

    @pytest.mark.parametrize("emotion", list(EMOTION_TO_FEATURES.keys()))
    def test_consonance_in_range(self, emotion: str) -> None:
        """consonance_target should be in [0, 1]."""
        profile = EMOTION_TO_FEATURES[emotion]
        assert 0.0 <= profile.consonance_target <= 1.0

    @pytest.mark.parametrize("emotion", list(EMOTION_TO_FEATURES.keys()))
    def test_spectral_centroid_in_range(self, emotion: str) -> None:
        """spectral_centroid_target should be in [0, 1]."""
        profile = EMOTION_TO_FEATURES[emotion]
        assert 0.0 <= profile.spectral_centroid_target <= 1.0

    @pytest.mark.parametrize("emotion", list(EMOTION_TO_FEATURES.keys()))
    def test_density_in_range(self, emotion: str) -> None:
        """density_target should be in [0, 1]."""
        profile = EMOTION_TO_FEATURES[emotion]
        assert 0.0 <= profile.density_target <= 1.0

    @pytest.mark.parametrize("emotion", list(EMOTION_TO_FEATURES.keys()))
    def test_register_height_in_range(self, emotion: str) -> None:
        """register_height should be in [0, 1]."""
        profile = EMOTION_TO_FEATURES[emotion]
        assert 0.0 <= profile.register_height <= 1.0


class TestEmotionDistinctions:
    """Verify that emotions in different quadrants differ meaningfully."""

    def test_triumphant_vs_melancholic(self) -> None:
        """Triumphant (high V, high A) vs melancholic (low V, low A) should differ."""
        t = EMOTION_TO_FEATURES["triumphant"]
        m = EMOTION_TO_FEATURES["melancholic"]
        # Triumphant: faster, major, louder, denser
        assert t.tempo_bpm_range[0] > m.tempo_bpm_range[0]
        assert t.major_minor_bias > m.major_minor_bias
        assert t.density_target > m.density_target

    def test_aggressive_vs_serene(self) -> None:
        """Aggressive (low V, high A) vs serene (high V, low A) should differ."""
        a = EMOTION_TO_FEATURES["aggressive"]
        s = EMOTION_TO_FEATURES["serene"]
        assert a.tempo_bpm_range[0] > s.tempo_bpm_range[0]
        assert a.consonance_target < s.consonance_target
        assert a.spectral_centroid_target > s.spectral_centroid_target

    def test_energetic_is_fastest(self) -> None:
        """Energetic should have one of the highest tempo ranges."""
        e = EMOTION_TO_FEATURES["energetic"]
        for name, p in EMOTION_TO_FEATURES.items():
            if name not in ("energetic", "aggressive"):
                assert e.tempo_bpm_range[1] >= p.tempo_bpm_range[0]


class TestGetFeatureProfile:
    """Tests for the lookup function."""

    def test_direct_match(self) -> None:
        """Direct emotion name should return the profile."""
        profile = get_feature_profile("melancholic")
        assert profile is not None
        assert profile.major_minor_bias < 0.3

    def test_synonym_match(self) -> None:
        """Common synonyms should resolve to a profile."""
        assert get_feature_profile("sad") is not None
        assert get_feature_profile("happy") is not None
        assert get_feature_profile("calm") is not None
        assert get_feature_profile("epic") is not None

    def test_case_insensitive(self) -> None:
        """Lookup should be case-insensitive."""
        assert get_feature_profile("TENDER") is not None
        assert get_feature_profile("Joyful") is not None

    def test_unknown_returns_none(self) -> None:
        """Unknown emotion should return None."""
        assert get_feature_profile("flibbertigibbet") is None


class TestEmotionToGeneratorParams:
    """Tests for the Conductor-facing interface."""

    def test_returns_dict_for_known_emotion(self) -> None:
        """Known emotion should return a dict with expected keys."""
        params = emotion_to_generator_params("melancholic")
        assert params is not None
        assert "tempo_bpm_range" in params
        assert "dynamics_low" in params
        assert "dynamics_high" in params
        assert "temperature_bias" in params
        assert "articulation" in params

    def test_returns_none_for_unknown(self) -> None:
        """Unknown emotion should return None."""
        assert emotion_to_generator_params("xyzzy") is None

    def test_temperature_bias_correlates_with_arousal(self) -> None:
        """Higher arousal emotions should have higher temperature bias."""
        energetic = emotion_to_generator_params("energetic")
        serene = emotion_to_generator_params("serene")
        assert energetic is not None and serene is not None
        assert energetic["temperature_bias"] > serene["temperature_bias"]


class TestAllEmotions:
    """Tests for the all_emotions utility."""

    def test_returns_sorted_list(self) -> None:
        """all_emotions() should return a sorted list."""
        emotions = all_emotions()
        assert emotions == sorted(emotions)
        assert len(emotions) == len(EMOTION_TO_FEATURES)

    def test_minimum_count(self) -> None:
        """Should have at least 16 emotions (4 per quadrant)."""
        assert len(all_emotions()) >= 16  # noqa: PLR2004
