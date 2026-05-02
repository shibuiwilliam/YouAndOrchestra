"""Tests for Dynamics Curve Renderer."""

from __future__ import annotations

from yao.generators.performance.dynamics_curve_renderer import DynamicsCurveRenderer
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score_with_sections() -> ScoreIR:
    pp_notes = tuple(
        Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=40, instrument="piano") for i in range(4)
    )
    ff_notes = tuple(
        Note(pitch=72, start_beat=float(i + 4), duration_beats=1.0, velocity=112, instrument="piano") for i in range(4)
    )
    return ScoreIR(
        title="Dynamics Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(name="intro", start_bar=0, end_bar=1, parts=(Part(instrument="piano", notes=pp_notes),)),
            Section(name="chorus", start_bar=1, end_bar=2, parts=(Part(instrument="piano", notes=ff_notes),)),
        ),
    )


class TestDynamicsCurveRenderer:
    def test_chorus_positive_dynamics(self) -> None:
        score = _make_score_with_sections()
        layer = DynamicsCurveRenderer().render(score)
        # Chorus notes should have positive micro_dynamics
        expr = layer.for_note(("piano", 4.0, 72))
        assert expr is not None
        assert expr.micro_dynamics > 0

    def test_intro_lower_dynamics(self) -> None:
        score = _make_score_with_sections()
        layer = DynamicsCurveRenderer().render(score)
        expr_intro = layer.for_note(("piano", 0.0, 60))
        expr_chorus = layer.for_note(("piano", 4.0, 72))
        assert expr_intro is not None
        assert expr_chorus is not None
        assert expr_intro.micro_dynamics < expr_chorus.micro_dynamics

    def test_values_in_range(self) -> None:
        score = _make_score_with_sections()
        layer = DynamicsCurveRenderer().render(score)
        for expr in layer.note_expressions.values():
            assert -1.0 <= expr.micro_dynamics <= 1.0

    def test_idempotent(self) -> None:
        score = _make_score_with_sections()
        r = DynamicsCurveRenderer()
        l1 = r.render(score)
        l2 = r.render(score)
        for nid in l1.note_expressions:
            assert l1.note_expressions[nid] == l2.note_expressions[nid]
