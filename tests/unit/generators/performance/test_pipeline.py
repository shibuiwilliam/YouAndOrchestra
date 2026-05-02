"""Tests for the Performance Realizer Pipeline."""

from __future__ import annotations

from yao.generators.performance.pipeline import realize_performance
from yao.ir.expression import PerformanceLayer
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score() -> ScoreIR:
    piano_notes = tuple(
        Note(pitch=60 + i, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano") for i in range(8)
    )
    violin_notes = tuple(
        Note(pitch=72 + i, start_beat=float(i), duration_beats=1.5, velocity=70, instrument="violin") for i in range(8)
    )
    return ScoreIR(
        title="Pipeline Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(
                name="verse",
                start_bar=0,
                end_bar=2,
                parts=(
                    Part(instrument="piano", notes=piano_notes),
                    Part(instrument="violin", notes=violin_notes),
                ),
            ),
        ),
    )


class TestPerformancePipeline:
    def test_produces_valid_layer(self) -> None:
        score = _make_score()
        layer = realize_performance(score, genre="jazz")
        assert isinstance(layer, PerformanceLayer)
        # Should have expressions for all notes
        assert len(layer.note_expressions) > 0

    def test_layer_validates(self) -> None:
        score = _make_score()
        layer = realize_performance(score)
        layer.validate()

    def test_idempotent(self) -> None:
        score = _make_score()
        l1 = realize_performance(score, genre="jazz")
        l2 = realize_performance(score, genre="jazz")
        for nid in l1.note_expressions:
            assert l1.note_expressions[nid] == l2.note_expressions[nid]

    def test_pedal_curves_for_piano(self) -> None:
        score = _make_score()
        layer = realize_performance(score)
        piano_pedals = layer.pedals_for_instrument("piano")
        assert len(piano_pedals) > 0
