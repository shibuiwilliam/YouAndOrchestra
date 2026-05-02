"""Tests for LilyPond writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.render.lilypond_writer import (
    _midi_to_lilypond_pitch,
    render_lilypond_pdf,
    write_lilypond,
)


@pytest.fixture()
def simple_score() -> ScoreIR:
    """4-note C major piano score."""
    notes = tuple(
        Note(
            pitch=60 + i * 2,
            start_beat=float(i),
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
        )
        for i in range(4)
    )
    return ScoreIR(
        title="LilyPond Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(
                name="verse",
                start_bar=0,
                end_bar=1,
                parts=(Part(instrument="piano", notes=notes),),
            ),
        ),
    )


class TestLilyPondPitchConversion:
    def test_middle_c(self) -> None:
        assert _midi_to_lilypond_pitch(60) == "c'"

    def test_c5(self) -> None:
        assert _midi_to_lilypond_pitch(72) == "c''"

    def test_a3(self) -> None:
        assert _midi_to_lilypond_pitch(57) == "a"

    def test_fis4(self) -> None:
        assert _midi_to_lilypond_pitch(66) == "fis'"

    def test_low_c(self) -> None:
        # C2 = MIDI 36
        assert _midi_to_lilypond_pitch(36) == "c,"


class TestLilyPondWriter:
    def test_writes_ly_file(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "test.ly"
        result = write_lilypond(simple_score, output)
        assert result.exists()
        content = output.read_text()
        assert len(content) > 0

    def test_ly_contains_header(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "header.ly"
        write_lilypond(simple_score, output)
        content = output.read_text()
        assert "\\header" in content
        assert "LilyPond Test" in content

    def test_ly_contains_notes(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "notes.ly"
        write_lilypond(simple_score, output)
        content = output.read_text()
        # Should contain at least middle C
        assert "c'" in content

    def test_ly_contains_key_and_time(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "key_time.ly"
        write_lilypond(simple_score, output)
        content = output.read_text()
        assert "\\key c \\major" in content
        assert "\\time 4/4" in content


class TestLilyPondPDFRendering:
    def test_pdf_skipped_without_lilypond(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        ly_path = tmp_path / "test.ly"
        write_lilypond(simple_score, ly_path)

        # If lilypond is not installed, should return None (not raise)
        import shutil

        if shutil.which("lilypond") is None:
            result = render_lilypond_pdf(ly_path)
            assert result is None
        else:
            # If lilypond IS installed, it should produce a PDF
            result = render_lilypond_pdf(ly_path)
            assert result is not None
            assert result.suffix == ".pdf"
