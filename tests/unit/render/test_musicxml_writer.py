"""Tests for MusicXML writer."""

from __future__ import annotations

from pathlib import Path

import music21
import pytest

from yao.ir.expression import NoteExpression, NoteId, PerformanceLayer
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.render.musicxml_writer import write_musicxml


@pytest.fixture()
def simple_score() -> ScoreIR:
    """8-note C major piano score."""
    notes = tuple(
        Note(
            pitch=60 + i,
            start_beat=float(i),
            duration_beats=1.0,
            velocity=80,
            instrument="piano",
        )
        for i in range(8)
    )
    return ScoreIR(
        title="MusicXML Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(
                name="verse",
                start_bar=0,
                end_bar=2,
                parts=(Part(instrument="piano", notes=notes),),
            ),
        ),
    )


@pytest.fixture()
def two_instrument_score() -> ScoreIR:
    """Score with piano and violin."""
    piano_notes = tuple(
        Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano") for i in range(4)
    )
    violin_notes = tuple(
        Note(pitch=72, start_beat=float(i), duration_beats=1.0, velocity=70, instrument="violin") for i in range(4)
    )
    return ScoreIR(
        title="Two Instruments",
        tempo_bpm=100.0,
        time_signature="3/4",
        key="G major",
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


class TestMusicXMLWriter:
    def test_writes_valid_musicxml(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "test.musicxml"
        result = write_musicxml(simple_score, output)
        assert result.exists()

        # Verify music21 can re-read it
        parsed = music21.converter.parse(str(output))
        assert parsed is not None

    def test_instruments_preserved(self, two_instrument_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "two_instr.musicxml"
        write_musicxml(two_instrument_score, output)

        parsed = music21.converter.parse(str(output))
        parts = list(parsed.parts)
        assert len(parts) == 2

    def test_key_signature(self, two_instrument_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "key.musicxml"
        write_musicxml(two_instrument_score, output)

        parsed = music21.converter.parse(str(output))
        keys = list(parsed.flatten().getElementsByClass(music21.key.Key))
        # Should have at least one key signature
        assert len(keys) >= 1

    def test_time_signature(self, two_instrument_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "time.musicxml"
        write_musicxml(two_instrument_score, output)

        parsed = music21.converter.parse(str(output))
        time_sigs = list(parsed.flatten().getElementsByClass(music21.meter.TimeSignature))
        assert len(time_sigs) >= 1
        assert time_sigs[0].ratioString == "3/4"

    def test_note_count_matches(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        output = tmp_path / "count.musicxml"
        write_musicxml(simple_score, output)

        parsed = music21.converter.parse(str(output))
        m21_notes = list(parsed.flatten().notes)
        assert len(m21_notes) == 8

    def test_with_performance_layer(self, simple_score: ScoreIR, tmp_path: Path) -> None:
        # Create a performance layer with an accent on the first note
        nid: NoteId = ("piano", 0.0, 60)
        perf = PerformanceLayer(
            note_expressions={nid: NoteExpression(accent_strength=0.8)},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )

        output = tmp_path / "expr.musicxml"
        write_musicxml(simple_score, output, performance_layer=perf)

        parsed = music21.converter.parse(str(output))
        m21_notes = list(parsed.flatten().notes)
        # At least one note should have an accent articulation
        accented = [n for n in m21_notes if any(isinstance(a, music21.articulations.Accent) for a in n.articulations)]
        assert len(accented) >= 1
