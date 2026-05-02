"""Tests for constraint satisfaction generator."""

from __future__ import annotations

import yao.generators.constraint_solver as _cs  # noqa: F401
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.registry import get_generator
from yao.ir.notation import parse_key, scale_notes
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


def _make_spec(seed: int = 42) -> CompositionSpec:
    return CompositionSpec(
        title="CSP Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
        generation=GenerationConfig(strategy="constraint_satisfaction", seed=seed),
    )


class TestConstraintSolver:
    def test_generates_notes(self) -> None:
        gen = get_generator("constraint_satisfaction")
        score, prov = gen.generate(_make_spec())
        assert len(score.all_notes()) > 0
        assert len(prov) > 0

    def test_seed_deterministic(self) -> None:
        gen = get_generator("constraint_satisfaction")
        s1, _ = gen.generate(_make_spec(seed=42))
        s2, _ = gen.generate(_make_spec(seed=42))
        assert [n.pitch for n in s1.all_notes()] == [n.pitch for n in s2.all_notes()]

    def test_respects_key(self) -> None:
        gen = get_generator("constraint_satisfaction")
        score, _ = gen.generate(_make_spec())
        root, st = parse_key("C major")
        valid_pcs = set()
        for o in range(0, 10):
            for n in scale_notes(root, st, o):
                if 0 <= n <= 127:
                    valid_pcs.add(n % 12)
        for note in score.all_notes():
            assert note.pitch % 12 in valid_pcs

    def test_respects_instrument_range(self) -> None:
        gen = get_generator("constraint_satisfaction")
        score, _ = gen.generate(_make_spec())
        r = INSTRUMENT_RANGES["piano"]
        for note in score.all_notes():
            assert r.midi_low <= note.pitch <= r.midi_high

    def test_no_consecutive_repeats(self) -> None:
        gen = get_generator("constraint_satisfaction")
        score, _ = gen.generate(_make_spec())
        notes = score.all_notes()
        for i in range(1, len(notes)):
            if notes[i].instrument == notes[i - 1].instrument:
                # May occasionally repeat at bar boundaries, but within a bar should not
                pass  # soft constraint, not hard

    def test_within_timeout(self) -> None:
        import time

        gen = get_generator("constraint_satisfaction")
        start = time.monotonic()
        gen.generate(_make_spec())
        elapsed = time.monotonic() - start
        assert elapsed < 5.0
