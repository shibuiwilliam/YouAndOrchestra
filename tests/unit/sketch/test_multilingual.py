"""Tests for multilingual SpecCompiler (Phase γ.7).

Tests cover:
- Japanese description produces valid spec (minor key, slow tempo, piano)
- Japanese instrument keywords (ピアノ, チェロ, etc.)
- Language auto-detection works for Japanese/English
- Backward compatibility: English descriptions still work
- Provenance records language detection
"""

from __future__ import annotations

from yao.sketch.compiler import SpecCompiler
from yao.sketch.language_detect import detect_language


class TestLanguageDetection:
    """Tests for language detection."""

    def test_japanese_text(self) -> None:
        assert detect_language("切ない 90 秒のピアノ曲") == "ja"

    def test_english_text(self) -> None:
        assert detect_language("a calm piano piece in D minor") == "en"

    def test_empty_text(self) -> None:
        assert detect_language("") == "en"

    def test_mixed_with_japanese_majority(self) -> None:
        """Text with substantial Japanese characters → ja."""
        assert detect_language("幻想的なアンビエント曲を作りたい") == "ja"

    def test_japanese_punctuation(self) -> None:
        """Japanese punctuation in mostly-ASCII text → ja."""
        assert detect_language("ambient、piano") == "ja"


class TestJapaneseCompilation:
    """Tests for Japanese spec compilation."""

    def test_setsunai_produces_minor_slow(self) -> None:
        """切ない (setsunai = wistful/melancholic) → minor, slow tempo."""
        compiler = SpecCompiler()
        spec, trajectory = compiler.compile(
            "切ない 90 秒のピアノ曲",
            "test-setsunai",
        )
        # Should detect Japanese
        assert any(r.parameters.get("language") == "ja" for r in compiler.provenance.records)
        # Should have piano
        assert any(i.name == "piano" for i in spec.instruments)
        # Duration should be ~90 seconds
        assert spec.total_bars > 0

    def test_piano_keyword_japanese(self) -> None:
        """ピアノ keyword produces piano instrument."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("ピアノの曲", "test-piano")
        assert any(i.name == "piano" for i in spec.instruments)

    def test_cello_keyword_japanese(self) -> None:
        """チェロ keyword produces cello instrument."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("チェロとピアノの曲", "test-cello")
        assert any(i.name == "cello" for i in spec.instruments)

    def test_slow_tempo_keyword(self) -> None:
        """ゆっくり (slowly) → slow tempo."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("ゆっくりしたピアノ曲", "test-slow")
        assert spec.tempo_bpm <= 80.0

    def test_fast_tempo_keyword(self) -> None:
        """速い (fast) → fast tempo."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("速いピアノ曲", "test-fast")
        assert spec.tempo_bpm >= 130.0

    def test_duration_seconds_japanese(self) -> None:
        """90秒 → 90 seconds duration."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("90秒のピアノ曲", "test-dur")
        beats = 90.0 * spec.tempo_bpm / 60.0
        expected_bars = max(8, round(beats / 4))
        assert spec.total_bars == expected_bars

    def test_duration_minutes_japanese(self) -> None:
        """2分 → 120 seconds duration."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("2分のピアノ曲", "test-dur-min")
        beats = 120.0 * spec.tempo_bpm / 60.0
        expected_bars = max(8, round(beats / 4))
        assert spec.total_bars == expected_bars

    def test_bpm_in_japanese_text(self) -> None:
        """BPM override in Japanese text."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("切ない 85BPM のピアノ曲", "test-bpm", language="ja")
        assert spec.tempo_bpm == 85.0

    def test_orchestra_keyword_japanese(self) -> None:
        """オーケストラ produces multiple instruments."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("オーケストラの壮大な曲", "test-orch")
        assert len(spec.instruments) >= 3


class TestEnglishBackwardCompatibility:
    """Tests that English compilation still works."""

    def test_english_calm_piano(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile(
            "a calm piano piece in D minor, 90 seconds",
            "test-en",
        )
        assert spec.key == "D minor"
        assert any(i.name == "piano" for i in spec.instruments)
        assert spec.tempo_bpm <= 85.0

    def test_english_cinematic(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile(
            "dramatic cinematic orchestral piece",
            "test-cinematic",
        )
        assert spec.genre == "cinematic"

    def test_provenance_records_language(self) -> None:
        """Provenance must record detected language."""
        compiler = SpecCompiler()
        compiler.compile("a calm piano piece", "test-prov")
        lang_records = [r for r in compiler.provenance.records if r.operation == "language_detection"]
        assert len(lang_records) == 1
        assert lang_records[0].parameters["language"] == "en"
