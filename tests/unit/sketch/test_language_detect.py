"""Tests for language detection."""

from __future__ import annotations

from yao.sketch.language_detect import detect_language


class TestLanguageDetect:
    """Tests for language auto-detection."""

    def test_english_text(self) -> None:
        assert detect_language("A calm piano piece for studying") == "en"

    def test_japanese_text(self) -> None:
        assert detect_language("雨の夜のカフェで聴きたい少し切ない曲") == "ja"

    def test_mixed_mostly_japanese(self) -> None:
        assert detect_language("切ないピアノ曲、90秒") == "ja"

    def test_mixed_mostly_english(self) -> None:
        assert detect_language("A calm piece with some piano") == "en"

    def test_empty_string(self) -> None:
        assert detect_language("") == "en"

    def test_whitespace_only(self) -> None:
        assert detect_language("   ") == "en"

    def test_japanese_punctuation(self) -> None:
        assert detect_language("test。") == "ja"

    def test_numbers_only(self) -> None:
        assert detect_language("12345") == "en"

    def test_katakana(self) -> None:
        assert detect_language("ドラマチックなオーケストラ") == "ja"

    def test_english_with_bpm(self) -> None:
        assert detect_language("epic orchestral 120 BPM") == "en"
