"""Tests for the loop-evolution generator.

Verifies:
- Generator registers correctly in the registry
- Produces valid ScoreIR with correct structure
- Respects loopable flag (boundary continuity)
- Blocks/arrangement string is parsed correctly
"""

from __future__ import annotations

import pytest

from yao.generators.loop_evolution import (
    LoopEvolutionConfig,
    LoopEvolutionGenerator,
    parse_arrangement,
)
from yao.generators.registry import available_generators, get_generator
from yao.ir.score_ir import ScoreIR
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.verify.seamlessness import evaluate_seamlessness


def _make_spec(
    arrangement: str = "A B",
    core_loop_bars: int = 4,
    seed: int = 42,
    temperature: float = 0.5,
) -> CompositionSpec:
    """Create a minimal composition spec for testing."""
    return CompositionSpec(
        title="Test Loop",
        key="C major",
        tempo_bpm=90.0,
        time_signature="4/4",
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="electric_bass", role="bass"),
        ],
        sections=[
            SectionSpec(name="loop_a", bars=4),
            SectionSpec(name="loop_b", bars=4),
        ],
        generation=GenerationConfig(
            strategy="loop_evolution",
            seed=seed,
            temperature=temperature,
        ),
    )


class TestLoopEvolutionRegistration:
    """Tests for generator registration."""

    def test_generator_is_registered(self) -> None:
        """The loop_evolution generator should be discoverable."""
        assert "loop_evolution" in available_generators()

    def test_get_generator_returns_instance(self) -> None:
        """get_generator('loop_evolution') returns a LoopEvolutionGenerator."""
        gen = get_generator("loop_evolution")
        assert isinstance(gen, LoopEvolutionGenerator)


class TestArrangementParsing:
    """Tests for arrangement string parsing."""

    def test_simple_arrangement(self) -> None:
        """Simple letter blocks parse correctly."""
        instruments = ["piano", "bass"]
        blocks = parse_arrangement("A B C", instruments)
        assert len(blocks) == 3
        assert blocks[0].label == "A"
        assert blocks[1].label == "B"
        assert blocks[2].label == "C"

    def test_drop_block_filters_instruments(self) -> None:
        """Drop block should only keep bass/rhythm instruments."""
        instruments = ["piano", "bass_guitar", "drums"]
        blocks = parse_arrangement("A drop A", instruments)
        assert len(blocks) == 3
        assert blocks[1].label == "drop"
        # Only bass and drums should be active in drop
        assert "piano" not in blocks[1].active_instruments
        assert "bass_guitar" in blocks[1].active_instruments
        assert "drums" in blocks[1].active_instruments

    def test_all_instruments_in_letter_block(self) -> None:
        """Letter blocks should include all instruments."""
        instruments = ["piano", "bass", "violin"]
        blocks = parse_arrangement("A", instruments)
        assert set(blocks[0].active_instruments) == {"piano", "bass", "violin"}

    def test_empty_arrangement_raises(self) -> None:
        """Empty arrangement string should raise SpecValidationError."""
        from yao.errors import SpecValidationError

        with pytest.raises(SpecValidationError):
            parse_arrangement("", ["piano"])

    def test_build_block_gradual(self) -> None:
        """Build blocks should gradually add instruments."""
        instruments = ["piano", "bass", "drums", "synth"]
        blocks = parse_arrangement("build build build build", instruments)
        # Each subsequent build block should have more instruments
        assert len(blocks[0].active_instruments) <= len(blocks[1].active_instruments)

    def test_case_insensitive(self) -> None:
        """Arrangement tokens should be case-insensitive."""
        instruments = ["piano"]
        blocks = parse_arrangement("a DROP b", instruments)
        assert blocks[0].label == "A"
        assert blocks[1].label == "drop"
        assert blocks[2].label == "B"


class TestLoopEvolutionGeneration:
    """Tests for the generation process."""

    def test_produces_valid_score_ir(self) -> None:
        """Generator should produce a valid ScoreIR."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        result = gen.generate(spec)

        assert isinstance(result, tuple)
        assert len(result) == 2
        score, prov = result
        assert isinstance(score, ScoreIR)
        assert isinstance(prov, ProvenanceLog)

    def test_score_has_correct_metadata(self) -> None:
        """ScoreIR should carry over spec metadata."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        score, _ = gen.generate(spec)

        assert score.title == "Test Loop"
        assert score.tempo_bpm == 90.0
        assert score.time_signature == "4/4"
        assert score.key == "C major"

    def test_score_has_sections(self) -> None:
        """Generated score should have sections matching spec."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        score, _ = gen.generate(spec)

        assert len(score.sections) == 2
        assert score.sections[0].name == "loop_a"
        assert score.sections[1].name == "loop_b"

    def test_score_has_notes(self) -> None:
        """Generated score should contain notes."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        score, _ = gen.generate(spec)

        all_notes = score.all_notes()
        assert len(all_notes) > 0

    def test_instruments_present(self) -> None:
        """All specified instruments should have notes."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        score, _ = gen.generate(spec)

        instruments = score.instruments()
        assert "piano" in instruments
        assert "electric_bass" in instruments

    def test_seed_reproducibility(self) -> None:
        """Same seed should produce same output."""
        spec = _make_spec(seed=123)
        gen = LoopEvolutionGenerator()
        score1, _ = gen.generate(spec)
        score2, _ = gen.generate(spec)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()
        assert len(notes1) == len(notes2)
        for n1, n2 in zip(notes1, notes2, strict=True):
            assert n1.pitch == n2.pitch
            assert n1.start_beat == n2.start_beat

    def test_different_seeds_different_output(self) -> None:
        """Different seeds should produce different output."""
        spec1 = _make_spec(seed=1)
        spec2 = _make_spec(seed=999)
        gen = LoopEvolutionGenerator()
        score1, _ = gen.generate(spec1)
        score2, _ = gen.generate(spec2)

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()
        # At least some notes should differ
        if len(notes1) == len(notes2):
            differs = any(n1.pitch != n2.pitch for n1, n2 in zip(notes1, notes2, strict=True))
            assert differs

    def test_provenance_records_decisions(self) -> None:
        """Provenance log should contain generation records."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        _, prov = gen.generate(spec)

        records = prov.records
        assert len(records) > 0
        # Should have start and complete records
        operations = [r.operation for r in records]
        assert "start_generation" in operations
        assert "complete_generation" in operations
        assert "generate_core_loops" in operations

    def test_custom_config(self) -> None:
        """Custom config should be respected."""
        config = LoopEvolutionConfig(core_loop_bars=2, arrangement="A B C")
        gen = LoopEvolutionGenerator(config=config)
        spec = _make_spec()
        # Add a third section for the arrangement
        spec = CompositionSpec(
            title=spec.title,
            key=spec.key,
            tempo_bpm=spec.tempo_bpm,
            time_signature=spec.time_signature,
            instruments=spec.instruments,
            sections=[
                SectionSpec(name="s1", bars=2),
                SectionSpec(name="s2", bars=2),
                SectionSpec(name="s3", bars=2),
            ],
            generation=spec.generation,
        )
        score, _ = gen.generate(spec)
        assert score.total_bars() == 6


class TestLoopBoundaryContinuity:
    """Tests for seamless loop boundaries."""

    def test_loopable_score_has_good_seamlessness(self) -> None:
        """A loop-generated score should have reasonable seamlessness."""
        spec = _make_spec(temperature=0.3)
        gen = LoopEvolutionGenerator(config=LoopEvolutionConfig(loopable=True))
        score, _ = gen.generate(spec)

        seamlessness = evaluate_seamlessness(score)
        # Loop generator should produce reasonably seamless output
        assert seamlessness >= 0.3

    def test_no_notes_past_boundary(self) -> None:
        """No notes should extend past the total duration."""
        spec = _make_spec()
        gen = LoopEvolutionGenerator()
        score, _ = gen.generate(spec)

        total_beats = score.total_beats()
        for note in score.all_notes():
            # Notes should not start after the end
            assert note.start_beat < total_beats + 0.01

    def test_empty_score_seamlessness(self) -> None:
        """Empty score should have perfect seamlessness."""
        from yao.ir.score_ir import ScoreIR

        empty = ScoreIR(
            title="Empty",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(),
        )
        assert evaluate_seamlessness(empty) == 1.0
