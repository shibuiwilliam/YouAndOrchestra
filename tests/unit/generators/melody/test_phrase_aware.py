"""Integration tests for PhraseAwareGenerator.

Tests the full M1→M2→M3→M4 pipeline end-to-end, verifying that it
produces well-formed ScoreIR with full provenance for all Tier-1 genres.
"""

from __future__ import annotations

import pytest

from yao.generators.melody.phrase_aware import PhraseAwareGenerator
from yao.generators.registry import get_generator
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)

TIER_1_GENRES = ["bebop_jazz", "j_pop_ballad", "classical_romantic", "lofi_hiphop", "rock_classic"]


def _make_spec(
    *,
    genre: str = "bebop_jazz",
    sections: list[tuple[str, int]] | None = None,
    seed: int = 42,
) -> CompositionSpec:
    """Create a CompositionSpec for testing."""
    if sections is None:
        sections = [("verse", 8), ("chorus", 8)]
    return CompositionSpec(
        title="Test Piece",
        genre=genre,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=b) for n, b in sections],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


class TestPhraseAwareGenerator:
    """Integration tests for the full phrase-first pipeline."""

    def test_basic_generation(self) -> None:
        """Generator produces (ScoreIR, ProvenanceLog)."""
        gen = PhraseAwareGenerator()
        spec = _make_spec()

        score, prov = gen.generate(spec)

        assert isinstance(score, ScoreIR)
        assert isinstance(prov, ProvenanceLog)

    def test_score_has_sections(self) -> None:
        """Output ScoreIR has the correct number of sections."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(sections=[("intro", 4), ("verse", 8), ("outro", 4)])

        score, _ = gen.generate(spec)

        assert len(score.sections) == 3
        assert score.sections[0].name == "intro"
        assert score.sections[1].name == "verse"
        assert score.sections[2].name == "outro"

    def test_score_has_notes(self) -> None:
        """Output ScoreIR contains notes."""
        gen = PhraseAwareGenerator()
        spec = _make_spec()

        score, _ = gen.generate(spec)

        all_notes = score.all_notes()
        assert len(all_notes) > 0

    def test_notes_in_valid_range(self) -> None:
        """All notes have valid MIDI values."""
        gen = PhraseAwareGenerator()
        spec = _make_spec()

        score, _ = gen.generate(spec)

        for note in score.all_notes():
            assert 0 <= note.pitch <= 127
            assert 0 <= note.velocity <= 127
            assert note.duration_beats > 0
            assert note.start_beat >= 0

    def test_provenance_has_all_layers(self) -> None:
        """Provenance contains entries from all four layers."""
        gen = PhraseAwareGenerator()
        spec = _make_spec()

        _, prov = gen.generate(spec)

        layers = {r.layer for r in prov.records}
        assert "M1_phrase_plan" in layers
        assert "M2_skeleton" in layers
        assert "M3_surface" in layers
        assert "M4_ornament" in layers
        assert "generator" in layers  # overall

    def test_provenance_all_have_agent(self) -> None:
        """All provenance entries have an agent identifier."""
        gen = PhraseAwareGenerator()
        spec = _make_spec()

        _, prov = gen.generate(spec)

        for record in prov.records:
            assert record.agent is not None

    def test_seed_reproducibility(self) -> None:
        """Same seed produces identical output."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(seed=999)

        score1, _ = gen.generate(spec)
        score2, _ = gen.generate(spec)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()

        assert len(notes1) == len(notes2)
        for n1, n2 in zip(notes1, notes2, strict=False):
            assert n1.pitch == n2.pitch
            assert n1.start_beat == n2.start_beat

    def test_different_seeds_differ(self) -> None:
        """Different seeds produce different output."""
        gen = PhraseAwareGenerator()
        spec1 = _make_spec(seed=1)
        spec2 = _make_spec(seed=2)

        score1, _ = gen.generate(spec1)
        score2, _ = gen.generate(spec2)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()

        # At least some pitches should differ
        if len(notes1) == len(notes2) and len(notes1) > 0:
            diffs = sum(1 for n1, n2 in zip(notes1, notes2, strict=False) if n1.pitch != n2.pitch)
            assert diffs > 0

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_generation_for_each_genre(self, genre: str) -> None:
        """Each Tier-1 genre generates a valid ScoreIR."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(genre=genre)

        score, prov = gen.generate(spec)

        assert isinstance(score, ScoreIR)
        assert len(score.all_notes()) > 0
        assert len(prov.records) >= 4  # at least M1, M2, M3, M4

    def test_score_metadata(self) -> None:
        """ScoreIR carries correct metadata from spec."""
        gen = PhraseAwareGenerator()
        spec = _make_spec()

        score, _ = gen.generate(spec)

        assert score.title == "Test Piece"
        assert score.tempo_bpm == 120.0
        assert score.time_signature == "4/4"
        assert score.key == "C major"

    def test_registry_integration(self) -> None:
        """PhraseAwareGenerator is accessible via the registry."""
        gen = get_generator("phrase_aware")
        assert isinstance(gen, PhraseAwareGenerator)

    def test_fallback_for_unknown_genre(self) -> None:
        """Unknown genre falls back to generic profile."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(genre="unknown_genre_xyz")

        score, prov = gen.generate(spec)

        assert len(score.all_notes()) > 0

    def test_single_section(self) -> None:
        """Works with a single section."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(sections=[("verse", 8)])

        score, _ = gen.generate(spec)

        assert len(score.sections) == 1
        assert score.sections[0].bar_count == 8

    def test_many_sections(self) -> None:
        """Works with many sections."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(
            sections=[
                ("intro", 4),
                ("verse1", 8),
                ("chorus", 8),
                ("verse2", 8),
                ("chorus2", 8),
                ("outro", 4),
            ]
        )

        score, _ = gen.generate(spec)

        assert len(score.sections) == 6
        total_notes = len(score.all_notes())
        assert total_notes > 0

    def test_short_piece(self) -> None:
        """Works with a very short piece (2 bars)."""
        gen = PhraseAwareGenerator()
        spec = _make_spec(sections=[("tag", 2)])

        score, _ = gen.generate(spec)

        assert len(score.all_notes()) > 0
