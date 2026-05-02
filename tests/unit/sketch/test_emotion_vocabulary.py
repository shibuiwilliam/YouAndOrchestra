"""Tests for emotion vocabulary loader."""

from __future__ import annotations

from yao.sketch.emotion_vocabulary import EmotionVocabulary


class TestEmotionVocabulary:
    """Tests for EmotionVocabulary loader and query."""

    def test_loads_japanese_emotions(self) -> None:
        vocab = EmotionVocabulary()
        assert vocab.word_count("ja") >= 50

    def test_loads_english_emotions(self) -> None:
        vocab = EmotionVocabulary()
        assert vocab.word_count("en") >= 20

    def test_lookup_japanese_word(self) -> None:
        vocab = EmotionVocabulary()
        entry = vocab.lookup("切ない", "ja")
        assert entry is not None
        assert entry.valence < 0
        assert entry.key == "A minor"
        assert entry.mode == "minor"

    def test_lookup_english_word(self) -> None:
        vocab = EmotionVocabulary()
        entry = vocab.lookup("happy", "en")
        assert entry is not None
        assert entry.valence > 0
        assert entry.mode == "major"

    def test_lookup_missing_word(self) -> None:
        vocab = EmotionVocabulary()
        assert vocab.lookup("nonexistent", "ja") is None

    def test_scan_text_japanese(self) -> None:
        vocab = EmotionVocabulary()
        matches = vocab.scan_text("雨の夜のカフェで聴きたい少し切ない曲", "ja")
        words = [m.word for m in matches]
        assert "切ない" in words

    def test_scan_text_multiple_matches(self) -> None:
        vocab = EmotionVocabulary()
        matches = vocab.scan_text("悲しいけど優しい曲", "ja")
        words = [m.word for m in matches]
        assert "悲しい" in words
        assert "優しい" in words

    def test_aggregate_empty(self) -> None:
        vocab = EmotionVocabulary()
        result = vocab.aggregate_emotions([])
        assert result["key"] == "C major"
        assert result["tempo_bpm"] == 120.0

    def test_aggregate_single(self) -> None:
        vocab = EmotionVocabulary()
        entry = vocab.lookup("悲しい", "ja")
        assert entry is not None
        result = vocab.aggregate_emotions([entry])
        assert "minor" in result["key"]
        assert result["mode"] == "minor"

    def test_aggregate_mixed_valence(self) -> None:
        vocab = EmotionVocabulary()
        sad = vocab.lookup("悲しい", "ja")
        gentle = vocab.lookup("優しい", "ja")
        assert sad is not None and gentle is not None
        result = vocab.aggregate_emotions([sad, gentle])
        # Mixed emotions → average valence should be near 0
        assert -0.5 < result["valence"] < 0.5

    def test_instruments_from_emotions(self) -> None:
        vocab = EmotionVocabulary()
        entry = vocab.lookup("壮大", "ja")
        assert entry is not None
        assert len(entry.instruments) > 0
        assert "strings_ensemble" in entry.instruments

    def test_valence_arousal_ranges(self) -> None:
        """All entries should have valence and arousal in [-1, 1]."""
        vocab = EmotionVocabulary()
        for lang in vocab.languages():
            for word in ["悲しい", "嬉しい", "激しい"] if lang == "ja" else ["happy", "sad", "epic"]:
                entry = vocab.lookup(word, lang)
                if entry:
                    assert -1.0 <= entry.valence <= 1.0, f"{word}: valence={entry.valence}"
                    assert -1.0 <= entry.arousal <= 1.0, f"{word}: arousal={entry.arousal}"
