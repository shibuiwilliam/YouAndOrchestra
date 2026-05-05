"""Tests for vocal track singability evaluation.

Verifies:
- Singability detects awkward leaps
- Singability detects tessitura strain
- Singability detects breath violations
- A well-written vocal line passes all checks
"""

from __future__ import annotations

import dataclasses

import pytest

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.singability import (
    SingabilityReport,
    evaluate_singability,
)


def _make_vocal_score(notes: list[Note], instrument: str = "voice") -> ScoreIR:
    """Create a minimal ScoreIR with a vocal part."""
    return ScoreIR(
        title="Vocal Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(
                name="verse",
                start_bar=0,
                end_bar=4,
                parts=(Part(instrument=instrument, notes=tuple(notes)),),
            ),
        ),
    )


class TestSingabilityAwkwardLeaps:
    """Tests for awkward leap detection."""

    def test_detects_large_leap(self) -> None:
        """An interval > 7 semitones should be flagged as awkward."""
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=72, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="voice"),
            # 12 semitone leap (octave) — awkward
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.awkward_leaps >= 1

    def test_no_leap_within_threshold(self) -> None:
        """Intervals <= 7 semitones should not be flagged."""
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=65, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=67, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="voice"),
            # All intervals <= 7
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.awkward_leaps == 0

    def test_multiple_leaps(self) -> None:
        """Multiple large leaps should all be counted."""
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=72, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=60, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="voice"),
            # Two 12-semitone leaps
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.awkward_leaps == 2


class TestSingabilityTessituraStrain:
    """Tests for tessitura strain detection."""

    def test_detects_high_strain(self) -> None:
        """Notes at extreme edges of the range should show strain."""
        # Voice range default: 48-79 (C3 to G5)
        # Strained zones: bottom 20% (48-54) and top 20% (73-79)
        notes = [
            Note(pitch=48, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=49, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=78, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=79, start_beat=3.0, duration_beats=1.0, velocity=80, instrument="voice"),
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        # All notes are in strained range
        assert report.tessitura_strain > 0.5

    def test_comfortable_range_no_strain(self) -> None:
        """Notes in the comfortable middle of the range should show no strain."""
        # Comfort zone for voice: roughly 55-72
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=64, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=65, start_beat=3.0, duration_beats=1.0, velocity=80, instrument="voice"),
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.tessitura_strain == 0.0


class TestSingabilityBreathViolations:
    """Tests for breath violation detection."""

    def test_detects_long_phrase(self) -> None:
        """A phrase > 8 beats without rest should be a breath violation."""
        # Continuous notes spanning 9 beats with no gap
        notes = [
            Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="voice") for i in range(10)
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.breath_violations >= 1

    def test_no_violation_with_rests(self) -> None:
        """Phrases with adequate breath opportunities should pass."""
        # Two short phrases with a breath gap between them
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=64, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="voice"),
            # Gap of 1 beat (breath opportunity)
            Note(pitch=65, start_beat=4.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=67, start_beat=5.0, duration_beats=1.0, velocity=80, instrument="voice"),
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.breath_violations == 0


class TestSingabilityWellWrittenLine:
    """Tests for a well-written vocal line passing all checks."""

    def test_good_vocal_line_passes(self) -> None:
        """A well-crafted vocal line should have a high score."""
        # Step-wise motion, comfortable range, adequate rests
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=75, instrument="voice"),
            Note(pitch=62, start_beat=1.0, duration_beats=1.0, velocity=75, instrument="voice"),
            Note(pitch=64, start_beat=2.0, duration_beats=1.0, velocity=80, instrument="voice"),
            Note(pitch=65, start_beat=3.0, duration_beats=1.0, velocity=80, instrument="voice"),
            # Breath
            Note(pitch=67, start_beat=5.0, duration_beats=1.0, velocity=75, instrument="voice"),
            Note(pitch=65, start_beat=6.0, duration_beats=1.0, velocity=75, instrument="voice"),
            Note(pitch=64, start_beat=7.0, duration_beats=1.5, velocity=70, instrument="voice"),
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        assert report.awkward_leaps == 0
        assert report.breath_violations == 0
        assert report.tessitura_strain == 0.0
        assert report.score >= 0.9

    def test_empty_vocal_part_is_perfect(self) -> None:
        """No notes = nothing wrong."""
        score = _make_vocal_score([])
        report = evaluate_singability(score, "voice")

        assert report.score == 1.0
        assert report.total_notes == 0

    def test_report_is_frozen_dataclass(self) -> None:
        """SingabilityReport should be immutable."""
        notes = [
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="voice"),
        ]
        score = _make_vocal_score(notes)
        report = evaluate_singability(score, "voice")

        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            report.awkward_leaps = 5  # type: ignore[misc]


class TestSingabilityVocalTypes:
    """Tests for different vocal types."""

    def test_soprano_range(self) -> None:
        """Soprano-specific range should be used when specified."""
        # Soprano range: 60-84
        # Note at 85 would be strained (above range)
        notes = [
            Note(pitch=83, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="soprano"),
            Note(pitch=84, start_beat=1.0, duration_beats=1.0, velocity=80, instrument="soprano"),
        ]
        score = _make_vocal_score(notes, instrument="soprano")
        report = evaluate_singability(score, "soprano")

        # These are at the top of soprano range — some strain expected
        assert report.tessitura_strain > 0.0

    def test_unknown_instrument_uses_default(self) -> None:
        """Unknown vocal instrument should use default voice range."""
        notes = [
            Note(pitch=64, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="custom_voice"),
        ]
        score = _make_vocal_score(notes, instrument="custom_voice")
        report = evaluate_singability(score, "custom_voice")

        # Should still produce a valid report
        assert isinstance(report, SingabilityReport)
        assert report.total_notes == 1
