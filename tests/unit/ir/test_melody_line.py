"""Tests for MelodyLine IR types: MelodyNote, OrnamentedNote, MelodyLine, OrnamentedMelodyLine."""

from __future__ import annotations

import pytest

from yao.ir.melody_line import MelodyLine, MelodyNote, OrnamentedMelodyLine, OrnamentedNote


class TestMelodyNote:
    """Tests for MelodyNote dataclass."""

    def test_creation(self) -> None:
        """MelodyNote created with required fields."""
        note = MelodyNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60)
        assert note.midi_pitch == 60
        assert note.velocity == 80

    def test_absolute_beat(self) -> None:
        """Absolute beat computed correctly."""
        note = MelodyNote(bar=3, beat=2.0, duration_beats=0.5, midi_pitch=64)
        assert note.absolute_beat == 14.0

    def test_end_beat(self) -> None:
        """End beat computed correctly."""
        note = MelodyNote(bar=0, beat=1.0, duration_beats=2.0, midi_pitch=60)
        assert note.end_beat == 3.0

    def test_frozen(self) -> None:
        """MelodyNote is immutable."""
        note = MelodyNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60)
        with pytest.raises(AttributeError):
            note.midi_pitch = 61  # type: ignore[misc]

    def test_note_types(self) -> None:
        """Various note types can be specified."""
        for ntype in ("chord_tone", "passing", "neighbor", "appoggiatura", "escape", "ghost"):
            note = MelodyNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60, note_type=ntype)
            assert note.note_type == ntype


class TestOrnamentedNote:
    """Tests for OrnamentedNote dataclass."""

    def test_creation(self) -> None:
        """OrnamentedNote created with defaults."""
        note = OrnamentedNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60)
        assert note.ornaments == ()
        assert note.articulation == "normal"
        assert note.micro_timing_offset_ms == 0.0
        assert note.velocity_modifier == 1.0

    def test_effective_velocity(self) -> None:
        """Effective velocity computed correctly and clamped."""
        note = OrnamentedNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60, velocity=100, velocity_modifier=1.5)
        assert note.effective_velocity == 127  # clamped

        quiet = OrnamentedNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60, velocity=50, velocity_modifier=0.5)
        assert quiet.effective_velocity == 25

    def test_with_ornaments(self) -> None:
        """OrnamentedNote with ornaments and articulation."""
        note = OrnamentedNote(
            bar=0,
            beat=0.0,
            duration_beats=1.0,
            midi_pitch=60,
            ornaments=("grace_note", "trill"),
            articulation="legato",
            micro_timing_offset_ms=-5.0,
        )
        assert len(note.ornaments) == 2
        assert note.articulation == "legato"
        assert note.micro_timing_offset_ms == -5.0


class TestMelodyLine:
    """Tests for MelodyLine dataclass."""

    def test_empty(self) -> None:
        """Empty melody line is valid."""
        ml = MelodyLine(notes=())
        assert ml.note_count == 0
        assert ml.pitch_range == (0, 0)

    def test_with_notes(self) -> None:
        """MelodyLine properties computed correctly."""
        notes = (
            MelodyNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=60),
            MelodyNote(bar=0, beat=1.0, duration_beats=1.0, midi_pitch=64),
            MelodyNote(bar=0, beat=2.0, duration_beats=1.0, midi_pitch=67),
        )
        ml = MelodyLine(notes=notes)
        assert ml.note_count == 3
        assert ml.pitch_range == (60, 67)


class TestOrnamentedMelodyLine:
    """Tests for OrnamentedMelodyLine dataclass."""

    def test_empty(self) -> None:
        """Empty ornamented melody line is valid."""
        oml = OrnamentedMelodyLine(notes=())
        assert oml.note_count == 0
        assert oml.pitch_range == (0, 0)

    def test_with_notes(self) -> None:
        """OrnamentedMelodyLine properties computed correctly."""
        notes = (
            OrnamentedNote(bar=0, beat=0.0, duration_beats=1.0, midi_pitch=55),
            OrnamentedNote(bar=0, beat=1.0, duration_beats=1.0, midi_pitch=72),
        )
        oml = OrnamentedMelodyLine(notes=notes)
        assert oml.note_count == 2
        assert oml.pitch_range == (55, 72)
