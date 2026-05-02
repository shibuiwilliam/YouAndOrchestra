"""Tests for Reaper RPP writer."""

from __future__ import annotations

from pathlib import Path

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.render.daw.reaper_writer import write_reaper_project


def _make_score() -> ScoreIR:
    notes = tuple(
        Note(pitch=60 + i, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano") for i in range(4)
    )
    return ScoreIR(
        title="RPP Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="v", start_bar=0, end_bar=1, parts=(Part(instrument="piano", notes=notes),)),),
    )


class TestReaperWriter:
    def test_writes_rpp_file(self, tmp_path: Path) -> None:
        output = tmp_path / "test.rpp"
        result = write_reaper_project(_make_score(), output)
        assert result.exists()
        content = output.read_text()
        assert "REAPER_PROJECT" in content

    def test_contains_track(self, tmp_path: Path) -> None:
        output = tmp_path / "track.rpp"
        write_reaper_project(_make_score(), output)
        content = output.read_text()
        assert "piano" in content

    def test_contains_tempo(self, tmp_path: Path) -> None:
        output = tmp_path / "tempo.rpp"
        write_reaper_project(_make_score(), output)
        content = output.read_text()
        assert "120" in content
