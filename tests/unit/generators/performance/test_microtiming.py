"""Tests for Microtiming Injector."""

from __future__ import annotations

from yao.generators.performance.microtiming_injector import MicrotimingInjector
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score() -> ScoreIR:
    notes = tuple(
        Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano") for i in range(4)
    )
    return ScoreIR(
        title="Microtiming Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="verse", start_bar=0, end_bar=1, parts=(Part(instrument="piano", notes=notes),)),),
    )


class TestMicrotimingInjector:
    def test_jazz_beats_2_4_delayed(self) -> None:
        score = _make_score()
        layer = MicrotimingInjector().inject(score, genre="jazz")
        # Beat 1.0 (beat 2 of bar) should be delayed
        expr = layer.for_note(("piano", 1.0, 60))
        assert expr is not None
        assert expr.micro_timing_ms > 0

    def test_default_near_zero(self) -> None:
        score = _make_score()
        layer = MicrotimingInjector().inject(score, genre="default")
        for expr in layer.note_expressions.values():
            assert abs(expr.micro_timing_ms) < 0.01

    def test_unknown_genre_no_crash(self) -> None:
        score = _make_score()
        layer = MicrotimingInjector().inject(score, genre="alien_music")
        assert len(layer.note_expressions) == 4

    def test_idempotent(self) -> None:
        score = _make_score()
        inj = MicrotimingInjector()
        l1 = inj.inject(score, "jazz")
        l2 = inj.inject(score, "jazz")
        for nid in l1.note_expressions:
            assert l1.note_expressions[nid] == l2.note_expressions[nid]
