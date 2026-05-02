"""Tests for CC Curve Generator."""

from __future__ import annotations

from yao.generators.performance.cc_curve_generator import CCCurveGenerator
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score(instrument: str) -> ScoreIR:
    notes = tuple(
        Note(pitch=60, start_beat=float(i), duration_beats=1.5, velocity=80, instrument=instrument) for i in range(4)
    )
    return ScoreIR(
        title="CC Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="verse", start_bar=0, end_bar=2, parts=(Part(instrument=instrument, notes=notes),)),),
    )


class TestCCCurveGenerator:
    def test_strings_vibrato(self) -> None:
        score = _make_score("violin")
        layer = CCCurveGenerator().generate(score)
        expr = layer.for_note(("violin", 0.0, 60))
        assert expr is not None
        assert expr.cc_curves is not None
        assert 1 in expr.cc_curves  # CC1 = vibrato

    def test_piano_pedal(self) -> None:
        score = _make_score("piano")
        layer = CCCurveGenerator().generate(score)
        assert len(layer.pedal_curves) > 0
        assert layer.pedal_curves[0].cc_number == 64

    def test_unknown_instrument_empty(self) -> None:
        score = _make_score("didgeridoo")
        layer = CCCurveGenerator().generate(score)
        # No CC curves for unknown instrument, but no crash
        assert len(layer.note_expressions) == 0

    def test_idempotent(self) -> None:
        score = _make_score("cello")
        gen = CCCurveGenerator()
        l1 = gen.generate(score)
        l2 = gen.generate(score)
        for nid in l1.note_expressions:
            assert l1.note_expressions[nid] == l2.note_expressions[nid]
