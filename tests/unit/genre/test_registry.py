"""Tests for GenreRegistry."""

from __future__ import annotations

import pytest

from yao.genre.profile import GenreProfile
from yao.genre.registry import GenreNotFoundError, GenreRegistry


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    """Reset the registry before each test."""
    GenreRegistry._cache.clear()
    GenreRegistry._loaded = False


class TestGenreRegistryLoading:
    """Test registry loading from disk."""

    def test_available_returns_sorted_names(self) -> None:
        """available() should return a sorted list of genre names."""
        names = GenreRegistry.available()
        assert names == sorted(names)
        assert len(names) > 0

    def test_all_returns_dict(self) -> None:
        """all() should return a dict of name -> GenreProfile."""
        profiles = GenreRegistry.all()
        assert isinstance(profiles, dict)
        for name, profile in profiles.items():
            assert isinstance(profile, GenreProfile)
            assert profile.name == name

    def test_get_existing_genre(self) -> None:
        """get() should return a GenreProfile for a known genre."""
        # We have pop.yaml, rock.yaml, jazz.yaml in genre/profiles/
        profile = GenreRegistry.get("pop")
        assert profile.name == "pop"
        assert profile.typical_tempo_range[0] >= 80

    def test_get_nonexistent_raises(self) -> None:
        """get() should raise GenreNotFoundError for unknown genre."""
        with pytest.raises(GenreNotFoundError, match="nonexistent_genre_xyz"):
            GenreRegistry.get("nonexistent_genre_xyz")

    def test_get_or_none_returns_none(self) -> None:
        """get_or_none() should return None for unknown genre."""
        result = GenreRegistry.get_or_none("nonexistent_genre_xyz")
        assert result is None

    def test_get_or_none_returns_profile(self) -> None:
        """get_or_none() should return a profile for known genre."""
        result = GenreRegistry.get_or_none("jazz")
        assert result is not None
        assert result.name == "jazz"


class TestGenreRegistryRegistration:
    """Test manual registration."""

    def test_register_custom_genre(self) -> None:
        """register() should add a new genre to the registry."""
        custom = GenreProfile(
            name="test_custom",
            typical_tempo_range=(100.0, 120.0),
            swing_8th=0.55,
        )
        GenreRegistry.register(custom)
        result = GenreRegistry.get("test_custom")
        assert result.name == "test_custom"
        assert result.swing_8th == 0.55

    def test_register_with_parent_resolves_inheritance(self) -> None:
        """register() should resolve inheritance when parent exists."""
        # First ensure jazz is loaded
        GenreRegistry.get("jazz")

        child = GenreProfile(
            name="test_bebop",
            parent="jazz",
            typical_tempo_range=(180.0, 300.0),
        )
        GenreRegistry.register(child)
        result = GenreRegistry.get("test_bebop")
        assert result.name == "test_bebop"
        assert result.typical_tempo_range == (180.0, 300.0)
        # Should inherit jazz's swing
        assert result.swing_8th == 0.67


class TestGenreRegistryReload:
    """Test cache management."""

    def test_reload_clears_and_reloads(self) -> None:
        """reload() should clear and reload all profiles."""
        initial_count = len(GenreRegistry.all())
        GenreRegistry.reload()
        reloaded_count = len(GenreRegistry.all())
        assert reloaded_count == initial_count


class TestGenreRegistryProfileContent:
    """Test that loaded profiles have expected content."""

    def test_jazz_has_swing(self) -> None:
        """Jazz profile should have triplet swing."""
        jazz = GenreRegistry.get("jazz")
        assert jazz.swing_8th >= 0.6

    def test_rock_has_straight_eighths(self) -> None:
        """Rock profile should have straight 8ths."""
        rock = GenreRegistry.get("rock")
        assert rock.swing_8th == 0.5

    def test_hip_hop_has_808_kit(self) -> None:
        """Hip-hop profile should prefer 808 kit."""
        hh = GenreRegistry.get("hip_hop")
        assert "808" in hh.drum_kit_preference

    def test_cinematic_has_wide_dynamics(self) -> None:
        """Cinematic profile should have wide dynamics range."""
        cin = GenreRegistry.get("cinematic")
        assert cin.typical_dynamics_range[0] == "pp"
        assert cin.typical_dynamics_range[1] == "fff"

    def test_all_profiles_have_names(self) -> None:
        """Every loaded profile must have a non-empty name."""
        for name, profile in GenreRegistry.all().items():
            assert profile.name, f"Profile {name} has empty name"
