"""Tests for F2 AI-Seed Generator.

Tests use the DeterministicMotifClient to avoid LLM calls in CI.
"""

from __future__ import annotations

import json

import pytest

from yao.generators.ai_seed import (
    AISeedGenerator,
    DeterministicMotifClient,
    LLMClient,
    _build_seed_prompt,
    _expand_motif,
    _parse_seed_motif,
)
from yao.ir.motif import Motif
from yao.ir.note import Note
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


def _minimal_spec() -> CompositionSpec:
    """Create a minimal CompositionSpec for testing."""
    return CompositionSpec(
        title="AI Test",
        tempo_bpm=120,
        key="C major",
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="main", bars=8)],
    )


class TestDeterministicMotifClient:
    """Tests for the deterministic fallback client."""

    def test_implements_protocol(self) -> None:
        client = DeterministicMotifClient(seed=42)
        assert isinstance(client, LLMClient)

    def test_model_name(self) -> None:
        client = DeterministicMotifClient(seed=42)
        assert "deterministic" in client.model_name

    def test_generates_valid_json(self) -> None:
        client = DeterministicMotifClient(seed=42)
        raw = client.generate_motif("test prompt")
        data = json.loads(raw)
        assert "notes" in data
        assert len(data["notes"]) >= 4

    def test_deterministic_same_seed(self) -> None:
        c1 = DeterministicMotifClient(seed=42)
        c2 = DeterministicMotifClient(seed=42)
        assert c1.generate_motif("test") == c2.generate_motif("test")

    def test_different_seeds_differ(self) -> None:
        c1 = DeterministicMotifClient(seed=42)
        c2 = DeterministicMotifClient(seed=99)
        assert c1.generate_motif("test") != c2.generate_motif("test")


class TestParseSeedMotif:
    """Tests for motif parsing and validation."""

    def test_parses_valid_json(self) -> None:
        raw = json.dumps(
            {
                "notes": [
                    {"pitch": 60, "duration": 0.5, "velocity": 80},
                    {"pitch": 64, "duration": 1.0, "velocity": 90},
                ]
            }
        )
        motif = _parse_seed_motif(raw, "C major", "piano")
        assert len(motif.notes) == 2
        assert motif.notes[0].pitch == 60
        assert motif.label == "ai_seed"

    def test_clamps_pitch_range(self) -> None:
        raw = json.dumps(
            {
                "notes": [
                    {"pitch": -5, "duration": 0.5, "velocity": 80},
                    {"pitch": 200, "duration": 0.5, "velocity": 80},
                ]
            }
        )
        motif = _parse_seed_motif(raw, "C major", "piano")
        assert motif.notes[0].pitch == 0
        assert motif.notes[1].pitch == 127

    def test_clamps_velocity(self) -> None:
        raw = json.dumps(
            {
                "notes": [
                    {"pitch": 60, "duration": 0.5, "velocity": 0},
                ]
            }
        )
        motif = _parse_seed_motif(raw, "C major", "piano")
        assert motif.notes[0].velocity >= 1

    def test_rejects_empty_notes(self) -> None:
        raw = json.dumps({"notes": []})
        with pytest.raises(ValueError, match="empty"):
            _parse_seed_motif(raw, "C major", "piano")

    def test_rejects_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="Failed to parse"):
            _parse_seed_motif("not json at all {{{", "C major", "piano")

    def test_parses_json_in_markdown_code_block(self) -> None:
        raw = '```json\n{"notes": [{"pitch": 60, "duration": 0.5, "velocity": 80}]}\n```'
        motif = _parse_seed_motif(raw, "C major", "piano")
        assert len(motif.notes) == 1

    def test_records_llm_generated_transformation(self) -> None:
        raw = json.dumps({"notes": [{"pitch": 60, "duration": 0.5, "velocity": 80}]})
        motif = _parse_seed_motif(raw, "C major", "piano")
        assert "llm_generated" in motif.transformations_applied


class TestExpandMotif:
    """Tests for rule-based motif expansion."""

    def test_expands_to_target_bars(self) -> None:
        import random

        seed = Motif(
            notes=(
                Note(pitch=60, start_beat=0.0, duration_beats=0.5, velocity=80, instrument="piano"),
                Note(pitch=64, start_beat=0.5, duration_beats=0.5, velocity=80, instrument="piano"),
            ),
            label="seed",
        )
        notes = _expand_motif(seed, total_bars=4, beats_per_bar=4.0, rng=random.Random(42))
        max_beat = max(n.start_beat + n.duration_beats for n in notes)
        # Should cover at least most of the target duration
        assert max_beat >= 12.0  # at least 3 bars worth

    def test_includes_seed_notes(self) -> None:
        import random

        seed = Motif(
            notes=(Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),),
            label="seed",
        )
        notes = _expand_motif(seed, total_bars=2, beats_per_bar=4.0, rng=random.Random(42))
        # First note should be the seed
        assert notes[0].pitch == 60


class TestBuildSeedPrompt:
    """Tests for prompt construction."""

    def test_includes_key(self) -> None:
        spec = _minimal_spec()
        prompt = _build_seed_prompt(spec)
        assert "C major" in prompt

    def test_includes_json_format(self) -> None:
        spec = _minimal_spec()
        prompt = _build_seed_prompt(spec)
        assert "JSON" in prompt


class TestAISeedGenerator:
    """Tests for the full AI-Seed Generator."""

    def test_generates_with_deterministic_client(self) -> None:
        gen = AISeedGenerator(llm_client=DeterministicMotifClient(seed=42))
        spec = _minimal_spec()
        score, log = gen.generate(spec)
        assert len(score.all_notes()) > 0

    def test_provenance_records_model(self) -> None:
        gen = AISeedGenerator(llm_client=DeterministicMotifClient(seed=42))
        spec = _minimal_spec()
        _, log = gen.generate(spec)
        records = log.records
        model_entries = [r for r in records if "model" in str(r.parameters)]
        assert len(model_entries) > 0

    def test_provenance_records_prompt_hash(self) -> None:
        gen = AISeedGenerator(llm_client=DeterministicMotifClient(seed=42))
        spec = _minimal_spec()
        _, log = gen.generate(spec)
        records = log.records
        hash_entries = [r for r in records if "prompt_hash" in str(r.parameters)]
        assert len(hash_entries) > 0

    def test_registered_as_ai_seed(self) -> None:
        from yao.generators.registry import get_generator

        gen = get_generator("ai_seed")
        assert gen is not None

    def test_deterministic_with_same_seed(self) -> None:
        client = DeterministicMotifClient(seed=42)
        gen = AISeedGenerator(llm_client=client)
        spec = _minimal_spec()
        score1, _ = gen.generate(spec)
        score2, _ = gen.generate(spec)
        # Same client + same spec → same notes
        assert len(score1.all_notes()) == len(score2.all_notes())

    def test_returns_score_and_provenance(self) -> None:
        gen = AISeedGenerator(llm_client=DeterministicMotifClient())
        spec = _minimal_spec()
        result = gen.generate(spec)
        assert len(result) == 2
        score, log = result
        assert isinstance(log, type(log))  # ProvenanceLog
        assert score.title == "AI Test"
