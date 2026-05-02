"""Tests for twelve-tone serial generator."""

from __future__ import annotations

import random

import yao.generators.twelve_tone as _tt  # noqa: F401
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.registry import get_generator
from yao.generators.twelve_tone import generate_row, inversion, prime, retrograde, retrograde_inversion
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _make_spec(seed: int = 42) -> CompositionSpec:
    return CompositionSpec(
        title="Serial Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="twelve_tone", seed=seed),
    )


class TestTwelveToneGeneration:
    def test_generates_notes(self) -> None:
        gen = get_generator("twelve_tone")
        score, prov = gen.generate(_make_spec())
        assert len(score.all_notes()) > 0
        assert len(prov) > 0

    def test_seed_deterministic(self) -> None:
        gen = get_generator("twelve_tone")
        s1, _ = gen.generate(_make_spec(seed=42))
        s2, _ = gen.generate(_make_spec(seed=42))
        assert [n.pitch for n in s1.all_notes()] == [n.pitch for n in s2.all_notes()]

    def test_different_seeds_different(self) -> None:
        gen = get_generator("twelve_tone")
        s1, _ = gen.generate(_make_spec(seed=1))
        s2, _ = gen.generate(_make_spec(seed=999))
        assert [n.pitch for n in s1.all_notes()] != [n.pitch for n in s2.all_notes()]

    def test_respects_instrument_range(self) -> None:
        gen = get_generator("twelve_tone")
        score, _ = gen.generate(_make_spec())
        piano_range = INSTRUMENT_RANGES["piano"]
        for note in score.all_notes():
            assert piano_range.midi_low <= note.pitch <= piano_range.midi_high


class TestToneRow:
    def test_row_has_12_unique_pitch_classes(self) -> None:
        rng = random.Random(42)
        row = generate_row(rng)
        assert len(row) == 12
        assert len(set(row)) == 12
        assert all(0 <= pc <= 11 for pc in row)

    def test_prime_is_identity(self) -> None:
        row = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        assert prime(row) == row

    def test_retrograde_reverses(self) -> None:
        row = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        assert retrograde(row) == list(reversed(row))

    def test_inversion_preserves_length(self) -> None:
        rng = random.Random(42)
        row = generate_row(rng)
        inv = inversion(row)
        assert len(inv) == 12
        # Inversion has all 12 pitch classes
        assert len(set(inv)) == 12

    def test_retrograde_inversion(self) -> None:
        rng = random.Random(42)
        row = generate_row(rng)
        ri = retrograde_inversion(row)
        assert len(ri) == 12
        assert ri == list(reversed(inversion(row)))

    def test_double_retrograde_is_identity(self) -> None:
        rng = random.Random(42)
        row = generate_row(rng)
        assert retrograde(retrograde(row)) == row
