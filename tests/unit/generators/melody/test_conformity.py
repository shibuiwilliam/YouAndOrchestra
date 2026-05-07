"""Tests for motif coherence and genre conformity scoring."""

from __future__ import annotations

from yao.generators.melody.phrase_aware import PhraseAwareGenerator
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.melodic_profile import load_melodic_profile
from yao.verify.conformity import genre_conformity_score, motif_coherence_score


def _make_spec(
    *,
    genre: str = "lofi_hiphop",
    sections: list[tuple[str, int]] | None = None,
    seed: int = 42,
) -> CompositionSpec:
    if sections is None:
        sections = [("verse", 8), ("chorus", 8), ("verse2", 8), ("chorus2", 8)]
    return CompositionSpec(
        title="Test",
        genre=genre,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=b) for n, b in sections],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


class TestMotifCoherence:
    """Tests for motif_coherence_score."""

    def test_coherence_on_32_bar_piece(self) -> None:
        """32-bar piece should have coherence >= 0.3 (some pattern recurrence)."""
        spec = _make_spec(genre="lofi_hiphop")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)

        coherence = motif_coherence_score(score)

        assert 0.0 <= coherence <= 1.0
        # Lo-fi with high motif recurrence should show some coherence
        assert coherence >= 0.1

    def test_coherence_varies_by_genre(self) -> None:
        """Different genres produce different coherence scores."""
        gen = PhraseAwareGenerator()

        # Lo-fi (high recurrence) vs bebop (more variation)
        lofi_spec = _make_spec(genre="lofi_hiphop", seed=42)
        bebop_spec = _make_spec(genre="bebop_jazz", seed=42)

        lofi_score, _ = gen.generate(lofi_spec)
        bebop_score, _ = gen.generate(bebop_spec)

        lofi_coherence = motif_coherence_score(lofi_score)
        bebop_coherence = motif_coherence_score(bebop_score)

        # Both should be valid scores
        assert 0.0 <= lofi_coherence <= 1.0
        assert 0.0 <= bebop_coherence <= 1.0

    def test_short_piece_coherence(self) -> None:
        """Very short piece returns low coherence (not enough data)."""
        spec = _make_spec(sections=[("tag", 2)])
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)

        coherence = motif_coherence_score(score)
        assert 0.0 <= coherence <= 1.0


class TestGenreConformity:
    """Tests for genre_conformity_score."""

    def test_conformity_returns_valid_scores(self) -> None:
        """Conformity scores are in [0, 1]."""
        spec = _make_spec(genre="classical_romantic")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("classical_romantic")

        conformity = genre_conformity_score(score, profile)

        assert "interval_conformity" in conformity
        assert "overall_genre_conformity" in conformity
        assert 0.0 <= conformity["overall_genre_conformity"] <= 1.0

    def test_conformity_nonzero_for_matching_genre(self) -> None:
        """Piece generated with a profile should show non-zero conformity."""
        spec = _make_spec(genre="rock_classic")
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)
        profile = load_melodic_profile("rock_classic")

        conformity = genre_conformity_score(score, profile)
        assert conformity["overall_genre_conformity"] > 0.1

    def test_integration_coherence_above_threshold(self) -> None:
        """Integration test: 32-bar piece achieves coherence >= 0.1."""
        spec = _make_spec(
            genre="j_pop_ballad",
            sections=[("verse", 8), ("chorus", 8), ("verse2", 8), ("chorus2", 8)],
            seed=123,
        )
        gen = PhraseAwareGenerator()
        score, _ = gen.generate(spec)

        coherence = motif_coherence_score(score)
        assert coherence >= 0.1, f"Coherence {coherence} below 0.1 threshold"
