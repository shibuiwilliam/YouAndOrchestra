"""Tests for UserStyleProfile."""

from __future__ import annotations

from pathlib import Path

from yao.reflect.style_profile import StylePreference, UserStyleProfile


class TestStyleProfile:
    def test_empty_profile(self) -> None:
        p = UserStyleProfile()
        assert p.user_id == "local"
        assert p.preferences == []

    def test_add_preference(self) -> None:
        p = UserStyleProfile()
        p.add_preference(StylePreference("tempo", (80, 120), 0.8, 5))
        assert p.get_preference("tempo") is not None
        assert p.get_preference("tempo").confidence == 0.8  # type: ignore[union-attr]

    def test_replace_preference(self) -> None:
        p = UserStyleProfile()
        p.add_preference(StylePreference("tempo", (80, 120), 0.5, 3))
        p.add_preference(StylePreference("tempo", (90, 130), 0.9, 10))
        assert len([x for x in p.preferences if x.dimension == "tempo"]) == 1
        assert p.get_preference("tempo").confidence == 0.9  # type: ignore[union-attr]

    def test_round_trip(self, tmp_path: Path) -> None:
        p = UserStyleProfile(user_id="test_user", total_annotations=10)
        p.add_preference(StylePreference("density", (0.3, 0.7), 0.85, 8))
        path = tmp_path / "profile.json"
        p.save(path)
        loaded = UserStyleProfile.load(path)
        assert loaded.user_id == "test_user"
        assert loaded.total_annotations == 10
        assert loaded.get_preference("density") is not None

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        loaded = UserStyleProfile.load(tmp_path / "missing.json")
        assert loaded.preferences == []
