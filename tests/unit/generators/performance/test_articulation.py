"""Tests for Articulation Realizer."""

from __future__ import annotations

from yao.generators.performance.articulation_realizer import ArticulationRealizer
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score(instrument: str = "violin") -> ScoreIR:
    notes = tuple(
        Note(pitch=60 + i, start_beat=float(i), duration_beats=1.0, velocity=80, instrument=instrument)
        for i in range(8)
    )
    return ScoreIR(
        title="Articulation Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="verse", start_bar=0, end_bar=2, parts=(Part(instrument=instrument, notes=notes),)),),
    )


class TestArticulationRealizer:
    def test_strong_beat_accent(self) -> None:
        score = _make_score("violin")
        layer = ArticulationRealizer().realize(score)
        # Beat 0.0 is a strong beat → should have accent
        expr = layer.for_note(("violin", 0.0, 60))
        assert expr is not None
        assert expr.accent_strength > 0

    def test_phrase_end_no_overlap(self) -> None:
        score = _make_score("violin")
        layer = ArticulationRealizer().realize(score)
        # Last note (beat 7) → phrase end → legato_overlap should be 0
        expr = layer.for_note(("violin", 7.0, 67))
        assert expr is not None
        assert expr.legato_overlap == 0.0

    def test_unknown_instrument_no_crash(self) -> None:
        score = _make_score("theremin")
        layer = ArticulationRealizer().realize(score)
        assert len(layer.note_expressions) == 8

    def test_idempotent(self) -> None:
        score = _make_score("piano")
        r = ArticulationRealizer()
        l1 = r.realize(score)
        l2 = r.realize(score)
        for nid in l1.note_expressions:
            assert l1.note_expressions[nid] == l2.note_expressions[nid]
