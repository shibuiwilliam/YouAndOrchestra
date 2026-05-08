"""Tests for melody-harmony alignment metric.

Phase 3.5 Step 6 — PROJECT.md §12.9.
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.melody_harmony_alignment import (
    AlignmentReport,
    evaluate_melody_harmony_alignment,
)


def _note(pitch: int, start_beat: float, duration: float = 1.0) -> Note:
    return Note(pitch=pitch, velocity=80, start_beat=start_beat, duration_beats=duration, instrument="piano")


def _make_score(notes: list[Note]) -> ScoreIR:
    """Helper to create a simple ScoreIR with one part."""
    part = Part(instrument="piano", notes=tuple(notes))
    section = Section(name="test", start_bar=0, end_bar=8, parts=(part,))
    return ScoreIR(
        title="test",
        tempo_bpm=120.0,
        key="C major",
        time_signature="4/4",
        sections=(section,),
    )


class TestAlignmentReport:
    def test_report_fields(self) -> None:
        report = AlignmentReport(overall=0.75, downbeat=0.85, note_count=10, downbeat_count=3)
        assert report.overall == 0.75
        assert report.downbeat == 0.85
        assert report.note_count == 10
        assert report.downbeat_count == 3


class TestEvaluateMelodyHarmonyAlignment:
    def test_empty_score(self) -> None:
        score = _make_score([])
        report = evaluate_melody_harmony_alignment(score)
        assert report.overall == 0.0
        assert report.note_count == 0

    def test_chord_tone_melody_scores_high(self) -> None:
        """A melody of pure chord tones should score well."""
        # C major chord tones: C=60, E=64, G=67
        notes = [_note(60, 0.0), _note(64, 1.0), _note(67, 2.0), _note(60, 4.0)]
        score = _make_score(notes)
        report = evaluate_melody_harmony_alignment(score)
        assert report.overall >= 0.7
        assert report.note_count == 4

    def test_downbeat_notes_tracked_separately(self) -> None:
        """Notes on beat 0 and beat 2 are tracked as downbeats."""
        notes = [_note(60, 0.0), _note(62, 1.0), _note(64, 2.0), _note(65, 3.0)]
        score = _make_score(notes)
        report = evaluate_melody_harmony_alignment(score)
        assert report.downbeat_count == 2
        assert report.note_count == 4

    def test_returns_float_scores(self) -> None:
        notes = [_note(60, 0.0)]
        score = _make_score(notes)
        report = evaluate_melody_harmony_alignment(score)
        assert isinstance(report.overall, float)
        assert isinstance(report.downbeat, float)
