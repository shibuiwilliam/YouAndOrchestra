"""Test that genre profiles have expected feature data."""

from __future__ import annotations

import pytest

from yao.schema.genre_profile_loader import load_unified_genre_profile
from yao.skills.loader import get_skill_registry

from .conftest import ALL_SKILL_GENRES


@pytest.mark.genre_coverage
class TestGenreOutputFeatures:
    """Verify genre profiles contain actionable data."""

    @pytest.mark.parametrize("genre_id", ALL_SKILL_GENRES)
    def test_has_tempo_range(self, genre_id: str) -> None:
        """Each genre should have a tempo range defined."""
        registry = get_skill_registry()
        profile = registry.get_genre(genre_id)
        assert profile is not None
        assert profile.tempo_range is not None
        lo, hi = profile.tempo_range
        assert lo > 0, f"Genre {genre_id} has invalid low tempo {lo}"
        assert hi >= lo, f"Genre {genre_id} has inverted tempo range"

    @pytest.mark.parametrize("genre_id", ALL_SKILL_GENRES)
    def test_has_preferred_instruments(self, genre_id: str) -> None:
        """Each genre should have at least one preferred instrument."""
        registry = get_skill_registry()
        profile = registry.get_genre(genre_id)
        assert profile is not None
        assert len(profile.preferred_instruments) > 0, f"Genre {genre_id} has no preferred instruments"

    @pytest.mark.parametrize("genre_id", ALL_SKILL_GENRES)
    def test_unified_profile_has_identity(self, genre_id: str) -> None:
        """Unified profile should have a non-empty identity."""
        profile = load_unified_genre_profile(genre_id)
        assert profile is not None
        assert profile.genre_id != ""
