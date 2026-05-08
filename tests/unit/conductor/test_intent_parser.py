"""Tests for IntentParser and IntentToSpec."""

from __future__ import annotations

from yao.conductor.intent_parser import IntentParser, StructuredIntent
from yao.conductor.intent_to_spec import IntentToSpec


class TestIntentParser:
    """Tests for the rule-based intent parser."""

    def test_basic_parse(self) -> None:
        """Parser produces a StructuredIntent with all fields."""
        parser = IntentParser()
        intent = parser.parse("a calm piano piece for studying, slightly nostalgic")

        assert isinstance(intent, StructuredIntent)
        assert -1.0 <= intent.valence <= 1.0
        assert 0.0 <= intent.arousal <= 1.0
        assert 0.0 <= intent.tension <= 1.0
        assert -1.0 <= intent.warmth <= 1.0
        assert 0.0 <= intent.nostalgia <= 1.0

    def test_happy_valence(self) -> None:
        """Happy keywords produce positive valence."""
        parser = IntentParser()
        intent = parser.parse("a happy, bright, cheerful celebration")
        assert intent.valence > 0

    def test_sad_valence(self) -> None:
        """Sad keywords produce negative valence."""
        parser = IntentParser()
        intent = parser.parse("a melancholy, somber, mournful requiem")
        assert intent.valence < 0

    def test_high_arousal(self) -> None:
        """Energetic keywords produce high arousal."""
        parser = IntentParser()
        intent = parser.parse("an intense, driving, powerful battle theme")
        assert intent.arousal > 0.5

    def test_low_arousal(self) -> None:
        """Calm keywords produce low arousal."""
        parser = IntentParser()
        intent = parser.parse("a peaceful, gentle, serene meditation")
        assert intent.arousal < 0.5

    def test_nostalgia_detection(self) -> None:
        """Nostalgic keywords increase nostalgia score."""
        parser = IntentParser()
        intent = parser.parse("nostalgic memories of childhood, vintage feel")
        assert intent.nostalgia > 0.5

    def test_genre_detection_jazz(self) -> None:
        """Jazz keywords detected correctly."""
        parser = IntentParser()
        intent = parser.parse("a bebop jazz tune with swing")
        genres = dict(intent.genre_candidates)
        assert "bebop_jazz" in genres

    def test_genre_detection_lofi(self) -> None:
        """Lo-fi keywords detected correctly."""
        parser = IntentParser()
        intent = parser.parse("chill lo-fi beats for studying")
        genres = dict(intent.genre_candidates)
        assert "lofi_hiphop" in genres

    def test_use_case_bgm(self) -> None:
        """BGM/study keywords produce bgm use case."""
        parser = IntentParser()
        intent = parser.parse("background music for studying")
        assert intent.use_case == "bgm"

    def test_use_case_game(self) -> None:
        """Game keywords produce game use case."""
        parser = IntentParser()
        intent = parser.parse("a puzzle game boss battle theme")
        assert intent.use_case == "game"

    def test_duration_seconds(self) -> None:
        """Explicit duration detected."""
        parser = IntentParser()
        intent = parser.parse("a 90 second piano piece")
        assert intent.duration_seconds == 90.0

    def test_duration_minutes(self) -> None:
        """Duration in minutes detected."""
        parser = IntentParser()
        intent = parser.parse("a 2 minute orchestral piece")
        assert intent.duration_seconds == 120.0

    def test_loopable_detection(self) -> None:
        """Loop keywords set loopable flag."""
        parser = IntentParser()
        intent = parser.parse("a looping background track")
        assert intent.loopable is True

    def test_instrument_detection(self) -> None:
        """Mentioned instruments are extracted."""
        parser = IntentParser()
        intent = parser.parse("a piece for piano and strings")
        assert "piano" in intent.instruments_mentioned
        assert "strings" in intent.instruments_mentioned

    def test_tempo_hint(self) -> None:
        """Tempo hints detected."""
        parser = IntentParser()
        intent = parser.parse("a fast, upbeat dance track")
        assert intent.tempo_hint == "fast"

    def test_mode_selection_happy(self) -> None:
        """Happy intent maps to major or lydian."""
        parser = IntentParser()
        intent = parser.parse("a bright, joyful, hopeful piece")
        mode = parser.select_mode(intent)
        assert mode in ("major", "lydian", "mixolydian", "pentatonic_major")

    def test_mode_selection_dark(self) -> None:
        """Dark intent maps to minor modes."""
        parser = IntentParser()
        intent = parser.parse("a dark, gloomy, ominous soundscape")
        mode = parser.select_mode(intent)
        assert mode in ("phrygian", "natural_minor", "harmonic_minor", "locrian")

    def test_mode_selection_nostalgic(self) -> None:
        """Nostalgic intent maps to dorian or pentatonic_minor."""
        parser = IntentParser()
        intent = parser.parse("a warm, nostalgic, bittersweet memory")
        mode = parser.select_mode(intent)
        assert mode in ("dorian", "pentatonic_minor", "blues", "natural_minor", "mixolydian")

    def test_complex_description(self) -> None:
        """Complex description populates all fields meaningfully."""
        parser = IntentParser()
        intent = parser.parse(
            "a calm summer evening, slightly melancholy but ultimately hopeful, "
            "90 seconds of gentle piano and strings, lo-fi aesthetic"
        )
        assert intent.duration_seconds == 90.0
        assert "piano" in intent.instruments_mentioned
        assert "strings" in intent.instruments_mentioned
        assert len(intent.mood_keywords) > 0


class TestIntentToSpec:
    """Tests for spec building from intent."""

    def test_basic_spec_building(self) -> None:
        """IntentToSpec produces a valid CompositionSpec."""
        parser = IntentParser()
        intent = parser.parse("a calm piano piece for studying, 90 seconds")
        builder = IntentToSpec()

        spec = builder.build_spec(intent)

        assert spec.title
        assert len(spec.instruments) > 0
        assert len(spec.sections) > 0
        assert spec.tempo_bpm > 0

    def test_spec_has_sections(self) -> None:
        """Spec sections cover the duration."""
        parser = IntentParser()
        intent = parser.parse("a 2 minute orchestral piece")
        builder = IntentToSpec()

        spec = builder.build_spec(intent)

        total_bars = sum(s.bars for s in spec.sections)
        assert total_bars >= 4

    def test_genre_in_spec(self) -> None:
        """Detected genre appears in spec."""
        parser = IntentParser()
        intent = parser.parse("a jazz bebop improvisation")
        builder = IntentToSpec()

        spec = builder.build_spec(intent)

        assert spec.genre in ("jazz", "bebop_jazz")

    def test_strategy_is_phrase_aware(self) -> None:
        """Strategy defaults to phrase_aware."""
        parser = IntentParser()
        intent = parser.parse("any piece")
        builder = IntentToSpec()

        spec = builder.build_spec(intent)

        assert spec.generation.strategy == "phrase_aware"

    def test_instruments_from_intent(self) -> None:
        """Instruments mentioned in intent appear in spec."""
        parser = IntentParser()
        intent = parser.parse("a piece for guitar and drums")
        builder = IntentToSpec()

        spec = builder.build_spec(intent)

        instrument_names = [i.name for i in spec.instruments]
        assert "guitar" in instrument_names
        assert "drums" in instrument_names

    def test_tempo_reflects_arousal(self) -> None:
        """High arousal produces faster tempo than low."""
        parser = IntentParser()
        calm = parser.parse("a peaceful, serene ambient piece")
        energetic = parser.parse("an intense, driving, fast rock anthem")
        builder = IntentToSpec()

        calm_spec = builder.build_spec(calm)
        energetic_spec = builder.build_spec(energetic)

        assert energetic_spec.tempo_bpm > calm_spec.tempo_bpm
