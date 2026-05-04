"""Tests for the unified GenreProfile schema."""

from __future__ import annotations

import pytest

from yao.errors import IncompleteGenreProfileError
from yao.schema.genre_profile import (
    GenreEvaluationSection,
    GenreHarmonySection,
    GenreIdentitySection,
    GenreTempoSection,
    UnifiedGenreProfile,
)
from yao.schema.genre_profile_loader import (
    all_unified_profiles,
    load_unified_genre_profile,
    reload_unified_profiles,
)


class TestUnifiedGenreProfileSchema:
    """Test the Pydantic model itself."""

    def test_minimal_construction(self) -> None:
        profile = UnifiedGenreProfile(genre_id="test")
        assert profile.genre_id == "test"
        assert profile.parent is None
        assert profile.evaluation.percussion_centric is False

    def test_full_construction(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="lofi_hiphop",
            parent="hip_hop",
            identity=GenreIdentitySection(name="Lo-fi Hip-Hop", family="hip-hop"),
            tempo=GenreTempoSection(central=82, range=(70, 95)),
            harmony=GenreHarmonySection(seventh_chord_probability=0.85),
            evaluation=GenreEvaluationSection(
                weights={"rhythm": 0.3, "melody": 0.15},
                percussion_centric=False,
            ),
        )
        assert profile.identity.name == "Lo-fi Hip-Hop"
        assert profile.tempo.central == 82
        assert profile.harmony.seventh_chord_probability == 0.85
        assert profile.evaluation.weights["rhythm"] == 0.3

    def test_validate_complete_passes(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="test",
            identity=GenreIdentitySection(name="Test Genre"),
            tempo=GenreTempoSection(range=(80, 120)),
        )
        profile.validate_complete()  # should not raise

    def test_validate_complete_fails_missing_name(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="test",
            tempo=GenreTempoSection(range=(80, 120)),
        )
        with pytest.raises(IncompleteGenreProfileError) as exc_info:
            profile.validate_complete()
        assert "identity.name" in exc_info.value.missing_sections

    def test_validate_complete_fails_missing_tempo(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="test",
            identity=GenreIdentitySection(name="Test"),
        )
        with pytest.raises(IncompleteGenreProfileError) as exc_info:
            profile.validate_complete()
        assert "tempo.range" in exc_info.value.missing_sections

    def test_tempo_range_from_list(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="test",
            tempo={"range": [80, 120]},
        )
        assert profile.tempo.range == (80.0, 120.0)

    def test_dynamics_range_from_list(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="test",
            typical_dynamics_range=["pp", "ff"],
        )
        assert profile.typical_dynamics_range == ("pp", "ff")

    def test_extra_fields_allowed(self) -> None:
        profile = UnifiedGenreProfile(
            genre_id="test",
            identity={"name": "Test", "custom_field": "value"},
        )
        assert profile.identity.name == "Test"


class TestUnifiedGenreProfileLoader:
    """Test loading from existing YAML sources."""

    def setup_method(self) -> None:
        reload_unified_profiles()

    def test_load_system1_jazz_ballad(self) -> None:
        profile = load_unified_genre_profile("jazz_ballad")
        assert profile is not None
        assert profile.genre_id == "jazz_ballad"
        assert profile.harmony.seventh_chord_probability == 0.90
        assert profile.tempo.range is not None
        assert profile.tempo.range[0] == 50.0

    def test_load_system1_lofi_hiphop(self) -> None:
        profile = load_unified_genre_profile("lofi_hiphop")
        assert profile is not None
        assert profile.genre_id == "lofi_hiphop"

    def test_load_system2_only_genre(self) -> None:
        """Genres in skills but not in genre_profiles/ should still load."""
        profile = load_unified_genre_profile("baroque")
        assert profile is not None
        assert profile.genre_id == "baroque"

    def test_load_nonexistent_returns_none(self) -> None:
        assert load_unified_genre_profile("nonexistent_genre_xyz") is None

    def test_all_system1_profiles_load(self) -> None:
        system1_genres = [
            "cinematic",
            "lofi_hiphop",
            "j_pop",
            "neoclassical",
            "ambient",
            "jazz_ballad",
            "game_8bit_chiptune",
            "acoustic_folk",
        ]
        for genre_id in system1_genres:
            profile = load_unified_genre_profile(genre_id)
            assert profile is not None, f"Failed to load {genre_id}"

    def test_all_unified_profiles_returns_all(self) -> None:
        profiles = all_unified_profiles()
        # Should have at least 8 from System 1 + extras from System 2
        assert len(profiles) >= 8
        assert "jazz_ballad" in profiles
        assert "lofi_hiphop" in profiles

    def test_caching_works(self) -> None:
        p1 = load_unified_genre_profile("jazz_ballad")
        p2 = load_unified_genre_profile("jazz_ballad")
        assert p1 is p2  # same object from cache

    def test_reload_clears_cache(self) -> None:
        p1 = load_unified_genre_profile("jazz_ballad")
        reload_unified_profiles()
        p2 = load_unified_genre_profile("jazz_ballad")
        assert p1 is not p2  # different objects after reload
