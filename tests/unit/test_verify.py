"""Tests for the verification layer."""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.analyzer import analyze_score
from yao.verify.music_lint import lint_score


class TestMusicLint:
    def test_valid_score_no_errors(self, sample_score_ir: ScoreIR) -> None:
        results = lint_score(sample_score_ir)
        errors = [r for r in results if r.severity == "error"]
        assert len(errors) == 0

    def test_detects_empty_score(self) -> None:
        empty = ScoreIR(
            title="Empty",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(),
        )
        results = lint_score(empty)
        rules = [r.rule for r in results]
        assert "empty_score" in rules

    def test_detects_out_of_range(self) -> None:
        bad_note = Note(
            pitch=10,  # Way below violin range (55-103)
            start_beat=0.0,
            duration_beats=1.0,
            velocity=80,
            instrument="violin",
        )
        part = Part(instrument="violin", notes=(bad_note,))
        section = Section(name="test", start_bar=0, end_bar=1, parts=(part,))
        score = ScoreIR(
            title="Out of Range",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )
        results = lint_score(score)
        range_errors = [r for r in results if r.rule == "note_out_of_range"]
        assert len(range_errors) == 1

    def test_detects_invalid_velocity(self) -> None:
        bad_note = Note(
            pitch=60,
            start_beat=0.0,
            duration_beats=1.0,
            velocity=0,  # 0 is invalid (1-127)
            instrument="piano",
        )
        part = Part(instrument="piano", notes=(bad_note,))
        section = Section(name="test", start_bar=0, end_bar=1, parts=(part,))
        score = ScoreIR(
            title="Bad Velocity",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )
        results = lint_score(score)
        velocity_errors = [r for r in results if r.rule == "invalid_velocity"]
        assert len(velocity_errors) == 1

    def test_detects_overlapping_notes(self) -> None:
        notes = (
            Note(pitch=60, start_beat=0.0, duration_beats=2.0, velocity=80, instrument="piano"),
            Note(pitch=60, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="piano"),
        )
        part = Part(instrument="piano", notes=notes)
        section = Section(name="test", start_bar=0, end_bar=1, parts=(part,))
        score = ScoreIR(
            title="Overlap",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )
        results = lint_score(score)
        overlap_warnings = [r for r in results if r.rule == "overlapping_notes"]
        assert len(overlap_warnings) == 1


class TestAnalyzer:
    def test_analyze_score_basic(self, sample_score_ir: ScoreIR) -> None:
        report = analyze_score(sample_score_ir)
        assert report.title == "Test Score"
        assert report.total_notes == 8
        assert report.tempo_bpm == 120.0
        assert "piano" in report.instruments_used
        assert report.notes_per_instrument["piano"] == 8

    def test_analyze_score_duration(self, sample_score_ir: ScoreIR) -> None:
        report = analyze_score(sample_score_ir)
        assert report.duration_seconds > 0

    def test_analyze_score_pitch_range(self, sample_score_ir: ScoreIR) -> None:
        report = analyze_score(sample_score_ir)
        assert report.pitch_range[0] == 60  # C4
        assert report.pitch_range[1] == 67  # G4

    def test_report_to_json(self, sample_score_ir: ScoreIR) -> None:
        report = analyze_score(sample_score_ir)
        json_str = report.to_json()
        assert "Test Score" in json_str
        assert "piano" in json_str

    def test_report_summary(self, sample_score_ir: ScoreIR) -> None:
        report = analyze_score(sample_score_ir)
        summary = report.summary()
        assert "Test Score" in summary
        assert "120.0 BPM" in summary

    def test_report_save(self, sample_score_ir: ScoreIR, tmp_output_dir: Path) -> None:  # noqa: F821

        report = analyze_score(sample_score_ir)
        path = tmp_output_dir / "analysis.json"
        report.save(path)
        assert path.exists()
        assert path.stat().st_size > 0
