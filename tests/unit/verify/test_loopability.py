"""Tests for F5 LoopabilityValidator."""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.loopability import LoopabilityValidator


def _make_loopable_score() -> ScoreIR:
    """A score designed to loop seamlessly: same rhythm/harmony at start and end."""
    notes = tuple(
        Note(
            pitch=60 + (i % 7),  # C major scale pattern
            start_beat=i * 0.5,
            duration_beats=0.5,
            velocity=80,
            instrument="piano",
        )
        for i in range(32)
    )
    return ScoreIR(
        title="loopable",
        tempo_bpm=120,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="A", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=notes),)),),
    )


def _make_non_loopable_score() -> ScoreIR:
    """A score with a harsh boundary: loud ending, quiet start, large leap."""
    end_notes = tuple(
        Note(pitch=90, start_beat=14.0 + i * 0.25, duration_beats=0.25, velocity=120, instrument="piano")
        for i in range(4)
    )
    start_notes = tuple(
        Note(pitch=40, start_beat=i * 2.0, duration_beats=1.0, velocity=30, instrument="piano") for i in range(2)
    )
    all_notes = start_notes + end_notes
    return ScoreIR(
        title="non_loopable",
        tempo_bpm=120,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="A", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=all_notes),)),),
    )


class TestLoopabilityValidator:
    """Tests for F5 LoopabilityValidator."""

    def test_loopable_score_high_overall(self) -> None:
        validator = LoopabilityValidator()
        report = validator.validate(_make_loopable_score())
        assert report.overall > 0.5

    def test_non_loopable_score_lower_overall(self) -> None:
        validator = LoopabilityValidator()
        loopable = validator.validate(_make_loopable_score())
        non_loopable = validator.validate(_make_non_loopable_score())
        assert loopable.overall > non_loopable.overall

    def test_non_loopable_has_issues(self) -> None:
        validator = LoopabilityValidator()
        report = validator.validate(_make_non_loopable_score())
        assert len(report.issues) > 0

    def test_empty_score_is_perfect(self) -> None:
        score = ScoreIR(title="empty", tempo_bpm=120, time_signature="4/4", key="C major", sections=())
        validator = LoopabilityValidator()
        report = validator.validate(score)
        assert report.overall == 1.0

    def test_report_dimensions_bounded(self) -> None:
        validator = LoopabilityValidator()
        report = validator.validate(_make_loopable_score())
        assert 0.0 <= report.rhythmic_continuity <= 1.0
        assert 0.0 <= report.harmonic_continuity <= 1.0
        assert 0.0 <= report.melodic_continuity <= 1.0
        assert 0.0 <= report.dynamic_continuity <= 1.0
        assert 0.0 <= report.overall <= 1.0

    def test_report_is_frozen(self) -> None:
        import pytest

        validator = LoopabilityValidator()
        report = validator.validate(_make_loopable_score())
        with pytest.raises(AttributeError):
            report.overall = 0.5  # type: ignore[misc]

    def test_melodic_leap_flagged(self) -> None:
        """Large pitch interval at boundary should lower melodic continuity."""
        validator = LoopabilityValidator()
        report = validator.validate(_make_non_loopable_score())
        assert report.melodic_continuity < 1.0

    def test_dynamic_jump_flagged(self) -> None:
        """Large velocity difference at boundary should lower dynamic continuity."""
        validator = LoopabilityValidator()
        report = validator.validate(_make_non_loopable_score())
        assert report.dynamic_continuity < 1.0
