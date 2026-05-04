"""Test that all genre profiles load and validate."""

from __future__ import annotations

import pytest

from yao.schema.genre_profile_loader import load_unified_genre_profile
from yao.skills.loader import get_skill_registry

from .conftest import ALL_SKILL_GENRES


@pytest.mark.genre_coverage
class TestGenreSchemaValidation:
    """Verify all genre profiles load without error."""

    @pytest.mark.parametrize("genre_id", ALL_SKILL_GENRES)
    def test_skill_genre_loads(self, genre_id: str) -> None:
        """Each genre in the skill registry loads as a skill profile."""
        registry = get_skill_registry()
        profile = registry.get_genre(genre_id)
        assert profile is not None, f"Skill genre '{genre_id}' not found"

    @pytest.mark.parametrize("genre_id", ALL_SKILL_GENRES)
    def test_unified_profile_loads(self, genre_id: str) -> None:
        """Each genre in the skill registry loads as a unified profile."""
        profile = load_unified_genre_profile(genre_id)
        assert profile is not None, f"Unified profile for '{genre_id}' not found"
        assert profile.genre_id != "", f"Genre '{genre_id}' has empty genre_id"

    def test_all_genres_count(self) -> None:
        """At least 8 genres exist."""
        assert len(ALL_SKILL_GENRES) >= 8, f"Only {len(ALL_SKILL_GENRES)} genres found"
