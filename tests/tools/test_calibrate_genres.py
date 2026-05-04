"""Tests for the genre calibration tool."""

from __future__ import annotations

import sys
from pathlib import Path

# Add tools to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))


class TestCalibrateGenres:
    """Test the genre calibration tool."""

    def test_calibrate_single_genre(self) -> None:
        from calibrate_genres import calibrate_genre

        result = calibrate_genre("jazz_ballad")
        assert result["genre_id"] == "jazz_ballad"
        assert result["status"] == "pass"
        assert result["has_unified_profile"] is True
        assert result["has_skill_profile"] is True

    def test_calibrate_nonexistent_genre(self) -> None:
        from calibrate_genres import calibrate_genre

        result = calibrate_genre("nonexistent_genre_xyz")
        assert result["status"] == "skip"

    def test_all_genres_pass(self) -> None:
        from calibrate_genres import calibrate_genre

        from yao.skills.loader import get_skill_registry

        registry = get_skill_registry()
        for genre_id in registry.list_genres():
            result = calibrate_genre(genre_id)
            assert result["status"] in ("pass", "skip"), f"Genre '{genre_id}' failed calibration: {result}"
