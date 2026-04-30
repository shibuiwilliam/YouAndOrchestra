"""Tests for the score diff module."""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.diff import diff_scores, format_diff


def _make_score(title: str, notes: tuple[Note, ...]) -> ScoreIR:
    """Helper to create a simple score."""
    part = Part(instrument="piano", notes=notes)
    section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
    return ScoreIR(
        title=title,
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


class TestDiffScores:
    def test_identical_scores_no_changes(self) -> None:
        notes = (Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),)
        score_a = _make_score("A", notes)
        score_b = _make_score("B", notes)
        diff = diff_scores(score_a, score_b)
        assert diff.total_changes == 0
        assert not diff.has_changes

    def test_added_notes(self) -> None:
        note1 = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        note2 = Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="piano")
        score_a = _make_score("A", (note1,))
        score_b = _make_score("B", (note1, note2))
        diff = diff_scores(score_a, score_b)
        assert len(diff.added_notes) == 1
        assert len(diff.removed_notes) == 0
        assert diff.added_notes[0].note.pitch == 62

    def test_removed_notes(self) -> None:
        note1 = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        note2 = Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="piano")
        score_a = _make_score("A", (note1, note2))
        score_b = _make_score("B", (note1,))
        diff = diff_scores(score_a, score_b)
        assert len(diff.removed_notes) == 1
        assert diff.removed_notes[0].note.pitch == 62

    def test_tempo_change(self) -> None:
        notes = (Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),)
        score_a = _make_score("A", notes)
        part = Part(instrument="piano", notes=notes)
        section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
        score_b = ScoreIR(
            title="B",
            tempo_bpm=140.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )
        diff = diff_scores(score_a, score_b)
        assert diff.tempo_changed

    def test_key_change(self) -> None:
        notes = (Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),)
        score_a = _make_score("A", notes)
        part = Part(instrument="piano", notes=notes)
        section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
        score_b = ScoreIR(
            title="B",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="G major",
            sections=(section,),
        )
        diff = diff_scores(score_a, score_b)
        assert diff.key_changed

    def test_modified_notes_pitch_change(self) -> None:
        note_a = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        note_b = Note(pitch=64, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        score_a = _make_score("A", (note_a,))
        score_b = _make_score("B", (note_b,))
        diff = diff_scores(score_a, score_b)
        assert len(diff.modified_notes) == 1
        assert diff.modified_notes[0].note_before.pitch == 60
        assert diff.modified_notes[0].note_after.pitch == 64
        assert "pitch" in diff.modified_notes[0].changes
        # Modified notes should NOT also appear as added/removed
        assert len(diff.added_notes) == 0
        assert len(diff.removed_notes) == 0

    def test_modified_notes_velocity_change(self) -> None:
        note_a = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        note_b = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=110, instrument="piano")
        score_a = _make_score("A", (note_a,))
        score_b = _make_score("B", (note_b,))
        diff = diff_scores(score_a, score_b)
        assert len(diff.modified_notes) == 1
        assert "velocity" in diff.modified_notes[0].changes


class TestFormatDiff:
    def test_format_no_changes(self) -> None:
        notes = (Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),)
        score_a = _make_score("A", notes)
        diff = diff_scores(score_a, score_a)
        output = format_diff(diff)
        assert "No changes" in output

    def test_format_with_changes(self) -> None:
        note1 = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        note2 = Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="piano")
        score_a = _make_score("A", (note1,))
        score_b = _make_score("B", (note1, note2))
        diff = diff_scores(score_a, score_b)
        output = format_diff(diff)
        assert "Added" in output
        assert "+1" in output
