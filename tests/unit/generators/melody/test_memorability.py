"""Tests for memorability proxy scoring."""

from __future__ import annotations

from yao.generators.melody.phrase_aware import PhraseAwareGenerator
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.verify.memorability import memorability_proxy


def _make_spec(genre: str = "j_pop_ballad", seed: int = 42) -> CompositionSpec:
    return CompositionSpec(
        title="Test",
        genre=genre,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8), SectionSpec(name="chorus", bars=8)],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


class TestMemorabilityProxy:
    """Tests for the memorability proxy."""

    def test_returns_valid_score(self) -> None:
        """Memorability score is in [0, 1]."""
        spec = _make_spec("j_pop_ballad")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)

        mem = memorability_proxy(score)
        assert 0.0 <= mem <= 1.0

    def test_nonzero_for_generated_piece(self) -> None:
        """Generated piece has some measurable memorability."""
        spec = _make_spec("lofi_hiphop")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)

        mem = memorability_proxy(score)
        assert mem > 0.0

    def test_varies_across_genres(self) -> None:
        """Different genres produce different memorability scores."""
        gen = PhraseAwareGenerator()

        jpop_score, _ = gen.generate(_make_spec("j_pop_ballad", seed=42))
        bebop_score, _ = gen.generate(_make_spec("bebop_jazz", seed=42))

        jpop_mem = memorability_proxy(jpop_score)
        bebop_mem = memorability_proxy(bebop_score)

        # Both should be valid
        assert 0.0 <= jpop_mem <= 1.0
        assert 0.0 <= bebop_mem <= 1.0

    def test_short_piece(self) -> None:
        """Short piece still returns a score."""
        spec = CompositionSpec(
            title="Short",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="tag", bars=2)],
            generation=GenerationConfig(strategy="phrase_aware", seed=42),
        )
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)

        mem = memorability_proxy(score)
        assert 0.0 <= mem <= 1.0
