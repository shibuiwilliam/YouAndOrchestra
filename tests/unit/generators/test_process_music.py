"""Tests for process music generator."""

from __future__ import annotations

import yao.generators.process_music as _pm  # noqa: F401
from yao.generators.registry import get_generator
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _make_spec(seed: int = 42, temperature: float = 0.5) -> CompositionSpec:
    return CompositionSpec(
        title="Process Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="process_music", seed=seed, temperature=temperature),
    )


class TestProcessMusicGeneration:
    def test_generates_notes(self) -> None:
        gen = get_generator("process_music")
        score, prov = gen.generate(_make_spec())
        assert len(score.all_notes()) > 0
        assert len(prov) > 0

    def test_seed_deterministic(self) -> None:
        gen = get_generator("process_music")
        s1, _ = gen.generate(_make_spec(seed=42))
        s2, _ = gen.generate(_make_spec(seed=42))
        assert [n.pitch for n in s1.all_notes()] == [n.pitch for n in s2.all_notes()]

    def test_respects_key(self) -> None:
        gen = get_generator("process_music")
        score, _ = gen.generate(_make_spec())
        # All notes should be from C major scale (pitch classes 0,2,4,5,7,9,11)
        c_major_pcs = {0, 2, 4, 5, 7, 9, 11}
        for note in score.all_notes():
            assert note.pitch % 12 in c_major_pcs

    def test_provenance_records_process_type(self) -> None:
        gen = get_generator("process_music")
        _, prov = gen.generate(_make_spec())
        start_rec = next(r for r in prov.records if r.operation == "start_generation")
        assert "process_type" in (start_rec.parameters or {})


class TestPhasing:
    def test_phasing_at_low_temperature(self) -> None:
        gen = get_generator("process_music")
        _, prov = gen.generate(_make_spec(temperature=0.1))
        start_rec = next(r for r in prov.records if r.operation == "start_generation")
        assert start_rec.parameters["process_type"] == "phasing"


class TestAdditive:
    def test_additive_at_medium_temperature(self) -> None:
        gen = get_generator("process_music")
        _, prov = gen.generate(_make_spec(temperature=0.5))
        start_rec = next(r for r in prov.records if r.operation == "start_generation")
        assert start_rec.parameters["process_type"] == "additive"

    def test_additive_note_count_increases(self) -> None:
        gen = get_generator("process_music")
        spec = _make_spec(temperature=0.5)
        score, _ = gen.generate(spec)
        notes = score.all_notes()
        # With additive, later bars should have more notes
        # Check first vs last bar note counts
        first_bar = [n for n in notes if n.start_beat < 4.0]
        last_bar = [n for n in notes if n.start_beat >= 28.0]
        assert len(last_bar) >= len(first_bar)


class TestSubtractive:
    def test_subtractive_at_high_temperature(self) -> None:
        gen = get_generator("process_music")
        _, prov = gen.generate(_make_spec(temperature=0.9))
        start_rec = next(r for r in prov.records if r.operation == "start_generation")
        assert start_rec.parameters["process_type"] == "subtractive"

    def test_subtractive_note_count_decreases(self) -> None:
        gen = get_generator("process_music")
        spec = _make_spec(temperature=0.9)
        score, _ = gen.generate(spec)
        notes = score.all_notes()
        # With subtractive, later bars should have fewer notes
        first_bar = [n for n in notes if n.start_beat < 4.0]
        last_bar = [n for n in notes if n.start_beat >= 28.0]
        assert len(last_bar) <= len(first_bar)
