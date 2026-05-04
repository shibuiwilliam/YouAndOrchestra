"""Tests for A/B Audition UI."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.audition.server import AuditionResult, SectionPreference


class TestSectionPreference:
    """Test SectionPreference dataclass."""

    def test_construction(self) -> None:
        pref = SectionPreference(section="chorus", preferred="a")
        assert pref.section == "chorus"
        assert pref.preferred == "a"
        assert pref.reason == ""

    def test_with_reason(self) -> None:
        pref = SectionPreference(section="verse", preferred="b", reason="better melody")
        assert pref.reason == "better melody"

    def test_frozen(self) -> None:
        pref = SectionPreference(section="intro", preferred="a")
        with pytest.raises(AttributeError):
            pref.section = "outro"  # type: ignore[misc]


class TestAuditionResult:
    """Test AuditionResult class."""

    def test_add_preference(self) -> None:
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        result.add_preference("chorus", "a")
        result.add_preference("verse", "b")
        assert len(result.preferences) == 2

    def test_preferred_count(self) -> None:
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        result.add_preference("chorus", "a")
        result.add_preference("verse", "a")
        result.add_preference("bridge", "b")
        counts = result.preferred_count()
        assert counts["a"] == 2
        assert counts["b"] == 1

    def test_winner_a(self) -> None:
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        result.add_preference("chorus", "a")
        result.add_preference("verse", "a")
        result.add_preference("bridge", "b")
        assert result.winner() == "a"

    def test_winner_b(self) -> None:
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        result.add_preference("chorus", "b")
        result.add_preference("verse", "b")
        assert result.winner() == "b"

    def test_winner_tied(self) -> None:
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        result.add_preference("chorus", "a")
        result.add_preference("verse", "b")
        assert result.winner() is None

    def test_empty_preferences(self) -> None:
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        assert result.winner() is None
        assert result.preferred_count() == {"a": 0, "b": 0}

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "prefs.json"
        result = AuditionResult(project="test", iteration_a="v001", iteration_b="v002")
        result.add_preference("chorus", "a", "better dynamics")
        result.add_preference("verse", "b")
        result.save(path)

        loaded = AuditionResult.load(path)
        assert loaded.project == "test"
        assert loaded.iteration_a == "v001"
        assert len(loaded.preferences) == 2
        assert loaded.preferences[0].reason == "better dynamics"
        assert loaded.winner() is None  # tied

    def test_create_audition_app_requires_fastapi(self) -> None:
        """Verify the app creation function exists and has correct signature."""
        import inspect

        from yao.audition.server import create_audition_app

        sig = inspect.signature(create_audition_app)
        params = list(sig.parameters.keys())
        assert "project" in params
        assert "iter_a_path" in params
        assert "iter_b_path" in params
        assert "output_path" in params
