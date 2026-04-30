"""Tests for intent.md schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.errors import SpecValidationError
from yao.schema.intent import IntentSpec


class TestIntentFromMarkdown:
    """Loading intent from markdown files."""

    def test_basic_intent(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("# My Song\n\nA calm piano piece for a rainy night cafe.")
        intent = IntentSpec.from_markdown(path)
        assert "calm" in intent.text
        assert "piano" in intent.keywords
        assert "calm" in intent.keywords
        assert intent.crystallized()

    def test_heading_stripped(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("# Title Here\n\nThe actual intent text.")
        intent = IntentSpec.from_markdown(path)
        assert "Title" not in intent.text
        assert "actual" in intent.text

    def test_no_heading(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("A bright, energetic pop track for a product demo.")
        intent = IntentSpec.from_markdown(path)
        assert "bright" in intent.keywords
        assert "energetic" in intent.keywords

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.md"
        with pytest.raises(SpecValidationError, match="not found"):
            IntentSpec.from_markdown(path)

    def test_empty_file_fails(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("")
        with pytest.raises(SpecValidationError, match="empty"):
            IntentSpec.from_markdown(path)

    def test_heading_only_fails(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("# Just a heading\n")
        with pytest.raises(SpecValidationError, match="no body"):
            IntentSpec.from_markdown(path)

    def test_too_long_fails(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("x " * 400)  # 800 chars
        with pytest.raises(SpecValidationError, match="600"):
            IntentSpec.from_markdown(path)


class TestCrystallized:
    """IntentSpec.crystallized() checks."""

    def test_crystallized_with_keywords(self) -> None:
        intent = IntentSpec(text="A calm piano piece", keywords=["calm", "piano"])
        assert intent.crystallized()

    def test_not_crystallized_with_one_keyword(self) -> None:
        intent = IntentSpec(text="Music", keywords=["music"])
        assert not intent.crystallized()

    def test_not_crystallized_empty(self) -> None:
        intent = IntentSpec(text="", keywords=[])
        assert not intent.crystallized()


class TestKeywordExtraction:
    """Keyword extraction heuristics."""

    def test_stop_words_removed(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("The bright and calm piece for the morning.")
        intent = IntentSpec.from_markdown(path)
        assert "the" not in intent.keywords
        assert "and" not in intent.keywords
        assert "bright" in intent.keywords

    def test_short_words_removed(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("An ok piece of art.")
        intent = IntentSpec.from_markdown(path)
        assert "ok" not in intent.keywords
        assert "art" in intent.keywords

    def test_deduplication(self, tmp_path: Path) -> None:
        path = tmp_path / "intent.md"
        path.write_text("Calm calm calm peaceful calm music.")
        intent = IntentSpec.from_markdown(path)
        assert intent.keywords.count("calm") == 1


class TestHintDefaults:
    """Hint fields default to None."""

    def test_defaults(self) -> None:
        intent = IntentSpec(text="test", keywords=[])
        assert intent.valence_hint is None
        assert intent.energy_hint is None
        assert intent.use_case_hint is None
