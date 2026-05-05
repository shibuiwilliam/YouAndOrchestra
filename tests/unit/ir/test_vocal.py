"""Tests for F6 Vocal IR — VocalNote, LyricsLine, and singing constraints."""

from __future__ import annotations

import pytest

from yao.ir.note import Note
from yao.ir.vocal import (
    LyricsLine,
    VocalNote,
    check_vocal_constraints,
)


def _make_note(pitch: int = 60, start: float = 0.0, dur: float = 1.0, vel: int = 80) -> Note:
    return Note(pitch=pitch, start_beat=start, duration_beats=dur, velocity=vel, instrument="vocal")


class TestVocalNote:
    """Tests for VocalNote."""

    def test_creation(self) -> None:
        vn = VocalNote(note=_make_note(), syllable="la")
        assert vn.syllable == "la"
        assert vn.pitch == 60
        assert vn.start_beat == 0.0

    def test_frozen(self) -> None:
        vn = VocalNote(note=_make_note(), syllable="la")
        with pytest.raises(AttributeError):
            vn.syllable = "do"  # type: ignore[misc]

    def test_is_syllabic(self) -> None:
        vn = VocalNote(note=_make_note(), syllable="la")
        assert vn.is_syllabic is True
        assert vn.is_melisma is False

    def test_is_melisma(self) -> None:
        vn = VocalNote(note=_make_note(), syllable=None)
        assert vn.is_melisma is True
        assert vn.is_syllabic is False

    def test_melisma_targets(self) -> None:
        vn = VocalNote(
            note=_make_note(),
            syllable="ah",
            melisma_target_pitches=(62, 64),
        )
        assert len(vn.melisma_target_pitches) == 2

    def test_breath_after(self) -> None:
        vn = VocalNote(note=_make_note(), syllable="la", breath_after=True)
        assert vn.breath_after is True

    def test_delegates_to_note(self) -> None:
        n = _make_note(pitch=72, start=2.0, dur=0.5, vel=100)
        vn = VocalNote(note=n, syllable="do")
        assert vn.pitch == 72
        assert vn.start_beat == 2.0
        assert vn.duration_beats == 0.5
        assert vn.velocity == 100


class TestLyricsLine:
    """Tests for LyricsLine."""

    def test_creation(self) -> None:
        line = LyricsLine(text="Hello world", syllables=("Hel", "lo", "world"))
        assert line.syllable_count == 3

    def test_frozen(self) -> None:
        line = LyricsLine(text="test", syllables=("test",))
        with pytest.raises(AttributeError):
            line.text = "changed"  # type: ignore[misc]

    def test_emphasis_must_match_syllables(self) -> None:
        with pytest.raises(ValueError, match="must match"):
            LyricsLine(
                text="Hello",
                syllables=("Hel", "lo"),
                rhythmic_emphasis=(1.0,),  # wrong length
            )

    def test_emphasis_matches(self) -> None:
        line = LyricsLine(
            text="Hello",
            syllables=("Hel", "lo"),
            rhythmic_emphasis=(1.0, 0.5),
        )
        assert len(line.rhythmic_emphasis) == 2

    def test_empty_emphasis_allowed(self) -> None:
        line = LyricsLine(text="test", syllables=("test",))
        assert line.rhythmic_emphasis == ()


class TestVocalConstraints:
    """Tests for F6 check_vocal_constraints."""

    def test_valid_vocal_line(self) -> None:
        vocal_notes = (
            VocalNote(note=_make_note(60, 0.0, 1.0), syllable="la"),
            VocalNote(note=_make_note(62, 1.0, 1.0), syllable="la"),
            VocalNote(note=_make_note(64, 2.0, 1.0), syllable="la"),
        )
        violations = check_vocal_constraints(vocal_notes)
        assert len(violations) == 0

    def test_too_short_syllable(self) -> None:
        vocal_notes = (
            VocalNote(note=_make_note(60, 0.0, 0.1), syllable="la"),  # too short
        )
        violations = check_vocal_constraints(vocal_notes)
        assert len(violations) == 1
        assert violations[0].rule == "min_syllable_duration"

    def test_melisma_no_duration_check(self) -> None:
        """Melisma notes (syllable=None) skip the min duration check."""
        vocal_notes = (
            VocalNote(note=_make_note(60, 0.0, 0.1), syllable=None),  # melisma, short is ok
        )
        violations = check_vocal_constraints(vocal_notes)
        assert len(violations) == 0

    def test_breath_without_rest(self) -> None:
        vocal_notes = (
            VocalNote(note=_make_note(60, 0.0, 1.0), syllable="la", breath_after=True),
            VocalNote(note=_make_note(62, 1.0, 1.0), syllable="la"),  # no gap
        )
        violations = check_vocal_constraints(vocal_notes)
        assert len(violations) == 1
        assert violations[0].rule == "breath_rest"

    def test_breath_with_sufficient_rest(self) -> None:
        vocal_notes = (
            VocalNote(note=_make_note(60, 0.0, 0.75), syllable="la", breath_after=True),
            VocalNote(note=_make_note(62, 1.0, 1.0), syllable="la"),  # 0.25 beat gap
        )
        violations = check_vocal_constraints(vocal_notes)
        assert len(violations) == 0

    def test_empty_returns_no_violations(self) -> None:
        violations = check_vocal_constraints(())
        assert len(violations) == 0

    def test_violation_has_location(self) -> None:
        vocal_notes = (VocalNote(note=_make_note(60, 4.5, 0.1), syllable="la"),)
        violations = check_vocal_constraints(vocal_notes)
        assert violations[0].bar == 1
        assert violations[0].beat == pytest.approx(0.5)
