"""Integration tests for MelodicProfile YAML loading.

Verifies that all 5 Tier-1 genre profiles load and validate correctly.
"""

from __future__ import annotations

import pytest

from yao.errors import SpecValidationError
from yao.schema.melodic_profile import load_melodic_profile

TIER_1_GENRES = [
    "bebop_jazz",
    "j_pop_ballad",
    "classical_romantic",
    "lofi_hiphop",
    "rock_classic",
]


class TestMelodicProfileLoading:
    """Tests for loading genre profiles from YAML."""

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_load_tier1_profile(self, genre: str) -> None:
        """Each Tier-1 profile loads without error."""
        profile = load_melodic_profile(genre)
        assert profile.genre == genre

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_profile_has_interval_distribution(self, genre: str) -> None:
        """Each profile has a non-empty interval distribution."""
        profile = load_melodic_profile(genre)
        assert len(profile.interval_distribution.distribution) > 0

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_profile_has_phrase_lengths(self, genre: str) -> None:
        """Each profile has a non-empty phrase length distribution."""
        profile = load_melodic_profile(genre)
        assert len(profile.phrase_length_distribution.distribution) > 0

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_profile_has_cadence_patterns(self, genre: str) -> None:
        """Each profile has at least one cadence pattern."""
        profile = load_melodic_profile(genre)
        assert len(profile.cadence_patterns) > 0

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_profile_has_anti_patterns(self, genre: str) -> None:
        """Each profile has at least one anti-pattern."""
        profile = load_melodic_profile(genre)
        assert len(profile.anti_patterns) > 0

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_profile_has_rhythm_templates(self, genre: str) -> None:
        """Each profile has at least one rhythm template."""
        profile = load_melodic_profile(genre)
        assert len(profile.rhythm_templates) > 0

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_profile_scalar_ranges(self, genre: str) -> None:
        """Scalar fields are within valid [0, 1] range."""
        profile = load_melodic_profile(genre)
        assert 0.0 <= profile.chord_tone_targeting <= 1.0
        assert 0.0 <= profile.chromaticism_level <= 1.0
        assert 0.0 <= profile.syncopation_level <= 1.0
        assert 0.0 <= profile.motif_recurrence_rate <= 1.0

    def test_nonexistent_genre_raises(self) -> None:
        """Loading a non-existent genre raises SpecValidationError."""
        with pytest.raises(SpecValidationError, match="No melodic profile found"):
            load_melodic_profile("nonexistent_genre_xyz")
