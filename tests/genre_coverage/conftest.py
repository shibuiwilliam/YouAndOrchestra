"""Shared fixtures for genre coverage tests."""

from __future__ import annotations

import pytest

from yao.schema.genre_profile_loader import reload_unified_profiles
from yao.skills.loader import get_skill_registry

# All genre IDs from the skill registry
ALL_SKILL_GENRES = sorted(get_skill_registry().list_genres())

# Genres that have matching drum patterns (can do full pipeline)
PIPELINE_GENRES = [
    "cinematic",
    "lofi_hiphop",
    "j_pop",
    "jazz_ballad",
    "ambient",
    "acoustic_folk",
    "neoclassical",
    "game_8bit_chiptune",
]


@pytest.fixture(autouse=True)
def _clear_profile_cache() -> None:
    """Clear the unified profile cache before each test."""
    reload_unified_profiles()
