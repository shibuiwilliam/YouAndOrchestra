"""Tests for Strudel emitter."""

from __future__ import annotations

from pathlib import Path

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.render.strudel_emitter import emit_strudel


def _make_score() -> ScoreIR:
    notes = tuple(
        Note(pitch=60 + i, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano") for i in range(4)
    )
    return ScoreIR(
        title="Strudel Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="v", start_bar=0, end_bar=1, parts=(Part(instrument="piano", notes=notes),)),),
    )


class TestStrudelEmitter:
    def test_returns_string(self) -> None:
        code = emit_strudel(_make_score())
        assert isinstance(code, str)
        assert "note(" in code

    def test_contains_title(self) -> None:
        code = emit_strudel(_make_score())
        assert "Strudel Test" in code

    def test_writes_file(self, tmp_path: Path) -> None:
        output = tmp_path / "test.js"
        emit_strudel(_make_score(), output)
        assert output.exists()
        assert "note(" in output.read_text()

    def test_contains_note_names(self) -> None:
        code = emit_strudel(_make_score())
        assert "c" in code.lower()
