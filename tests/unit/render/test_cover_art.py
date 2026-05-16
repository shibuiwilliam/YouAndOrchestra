"""Tests for the cover art generator."""

from __future__ import annotations

from pathlib import Path

from yao.render.cover_art import (
    CoverArtRequest,
    CoverArtResult,
    _build_prompt,
    generate_cover_art,
)


class TestBuildPrompt:
    """Tests for prompt construction from musical metadata."""

    def test_includes_title(self) -> None:
        """Prompt should include the composition title."""
        request = CoverArtRequest(title="Midnight Jazz")
        prompt = _build_prompt(request)
        assert "Midnight Jazz" in prompt

    def test_jazz_genre_style(self) -> None:
        """Jazz genre should produce smoky nightclub visuals."""
        request = CoverArtRequest(title="Test", genre="jazz_bebop")
        prompt = _build_prompt(request)
        assert "smoky" in prompt.lower() or "nightclub" in prompt.lower()

    def test_electronic_genre_style(self) -> None:
        """Electronic genre should produce neon/futuristic visuals."""
        request = CoverArtRequest(title="Test", genre="electronic_house")
        prompt = _build_prompt(request)
        assert "neon" in prompt.lower() or "futuristic" in prompt.lower()

    def test_minor_key_cool_colors(self) -> None:
        """Minor key should suggest cool color palette."""
        request = CoverArtRequest(title="Test", key="A minor")
        prompt = _build_prompt(request)
        assert "cool" in prompt.lower() or "darker" in prompt.lower()

    def test_major_key_warm_colors(self) -> None:
        """Major key should suggest warm color palette."""
        request = CoverArtRequest(title="Test", key="C major")
        prompt = _build_prompt(request)
        assert "warm" in prompt.lower() or "bright" in prompt.lower()

    def test_slow_tempo_calm(self) -> None:
        """Slow tempo should suggest calm energy."""
        request = CoverArtRequest(title="Test", tempo_bpm=60.0)
        prompt = _build_prompt(request)
        assert "calm" in prompt.lower() or "contemplative" in prompt.lower()

    def test_fast_tempo_intense(self) -> None:
        """Fast tempo should suggest high energy."""
        request = CoverArtRequest(title="Test", tempo_bpm=180.0)
        prompt = _build_prompt(request)
        assert "energy" in prompt.lower() or "intense" in prompt.lower()

    def test_style_hint_included(self) -> None:
        """User style hint should appear in prompt."""
        request = CoverArtRequest(title="Test", style_hint="watercolor painting")
        prompt = _build_prompt(request)
        assert "watercolor painting" in prompt

    def test_mood_included(self) -> None:
        """Mood should appear in prompt."""
        request = CoverArtRequest(title="Test", mood="melancholic")
        prompt = _build_prompt(request)
        assert "melancholic" in prompt

    def test_no_text_instruction(self) -> None:
        """Prompt should instruct no text in image."""
        request = CoverArtRequest(title="Test")
        prompt = _build_prompt(request)
        assert "no text" in prompt.lower() or "No text" in prompt

    def test_square_aspect_ratio(self) -> None:
        """Prompt should request square aspect ratio."""
        request = CoverArtRequest(title="Test")
        prompt = _build_prompt(request)
        assert "1:1" in prompt or "square" in prompt.lower()


class TestGenerateCoverArt:
    """Tests for the generate function (without API calls)."""

    def test_missing_api_key_returns_error(self, monkeypatch: object, tmp_path: Path) -> None:
        """Should fail gracefully without API key."""
        import os

        # Ensure no API key is set
        env = os.environ.copy()
        env.pop("GOOGLE_API_KEY", None)
        os.environ.clear()
        os.environ.update(env)

        request = CoverArtRequest(title="Test")
        result = generate_cover_art(request, tmp_path / "test.png")
        assert not result.success
        assert "GOOGLE_API_KEY" in result.error_message

    def test_result_dataclass_defaults(self) -> None:
        """CoverArtResult should have sensible defaults."""
        result = CoverArtResult()
        assert result.image_path is None
        assert result.success is False
        assert result.prompt_used == ""
        assert result.model == ""
