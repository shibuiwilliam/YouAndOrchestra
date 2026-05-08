"""Tests for genre conformance feedback adaptations."""

from __future__ import annotations

from yao.conductor.feedback import suggest_genre_adaptations
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.verify.genre_conformance import GenreConformanceScore


def _make_spec(genre: str = "jazz", tempo: float = 120.0) -> CompositionSpec:
    """Create a minimal CompositionSpec for testing."""
    return CompositionSpec(
        title="test",
        genre=genre,
        tempo_bpm=tempo,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="A", bars=4)],
        generation=GenerationConfig(temperature=0.5),
    )


class TestGenreFeedback:
    """Test genre conformance → feedback adaptations."""

    def test_no_adaptations_when_conformance_high(self) -> None:
        """No adaptations when all dimensions pass."""
        score = GenreConformanceScore(
            genre="jazz",
            instrumentation_match=0.9,
            tempo_match=1.0,
            rhythm_match=0.8,
            harmony_match=0.7,
            form_match=0.5,
            overall=0.8,
        )
        adaptations = suggest_genre_adaptations(score, _make_spec())
        assert len(adaptations) == 0

    def test_tempo_adaptation_when_out_of_range(self) -> None:
        """Low tempo match should suggest tempo change."""
        score = GenreConformanceScore(
            genre="jazz",
            instrumentation_match=0.9,
            tempo_match=0.2,
            rhythm_match=0.8,
            harmony_match=0.7,
            form_match=0.5,
            overall=0.6,
        )
        adaptations = suggest_genre_adaptations(score, _make_spec())
        tempo_adaptations = [a for a in adaptations if a.field == "tempo_bpm"]
        assert len(tempo_adaptations) == 1
        assert "outside genre range" in tempo_adaptations[0].reason

    def test_instrumentation_adaptation(self) -> None:
        """Low instrumentation match should suggest adding instruments."""
        score = GenreConformanceScore(
            genre="rock",
            instrumentation_match=0.2,
            tempo_match=1.0,
            rhythm_match=0.8,
            harmony_match=0.7,
            form_match=0.5,
            overall=0.6,
        )
        adaptations = suggest_genre_adaptations(score, _make_spec(genre="rock"))
        instr_adaptations = [a for a in adaptations if a.field == "instruments"]
        assert len(instr_adaptations) == 1

    def test_harmony_adaptation(self) -> None:
        """Low harmony match should suggest temperature increase."""
        score = GenreConformanceScore(
            genre="jazz",
            instrumentation_match=0.9,
            tempo_match=1.0,
            rhythm_match=0.8,
            harmony_match=0.3,
            form_match=0.5,
            overall=0.6,
        )
        adaptations = suggest_genre_adaptations(score, _make_spec())
        temp_adaptations = [a for a in adaptations if "temperature" in a.field]
        assert len(temp_adaptations) == 1

    def test_multiple_failures_produce_multiple_adaptations(self) -> None:
        """Multiple failing dimensions should produce multiple adaptations."""
        score = GenreConformanceScore(
            genre="jazz",
            instrumentation_match=0.2,
            tempo_match=0.1,
            rhythm_match=0.3,
            harmony_match=0.2,
            form_match=0.5,
            overall=0.25,
        )
        adaptations = suggest_genre_adaptations(score, _make_spec())
        assert len(adaptations) >= 3
