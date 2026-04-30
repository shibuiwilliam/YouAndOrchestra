"""Tests for the intermediate representation layer."""

from __future__ import annotations

import pytest

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.errors import RangeViolationError, SpecValidationError
from yao.ir.notation import midi_to_note_name, note_name_to_midi, parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import bars_to_beats, beats_to_seconds, beats_to_ticks, ticks_to_beats


class TestNote:
    def test_note_is_frozen(self) -> None:
        note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        with pytest.raises(AttributeError):
            note.pitch = 61  # type: ignore[misc]

    def test_end_beat(self) -> None:
        note = Note(pitch=60, start_beat=2.0, duration_beats=1.5, velocity=80, instrument="piano")
        assert note.end_beat() == 3.5

    def test_range_validation_passes(self) -> None:
        note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        note.validate_range()  # Should not raise

    def test_range_validation_fails(self) -> None:
        note = Note(pitch=130, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="violin")
        with pytest.raises(RangeViolationError) as exc_info:
            note.validate_range()
        assert exc_info.value.instrument == "violin"
        assert exc_info.value.note == 130

    def test_range_validation_with_explicit_range(self) -> None:
        note = Note(pitch=20, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        with pytest.raises(RangeViolationError):
            note.validate_range(INSTRUMENT_RANGES["piano"])

    def test_unknown_instrument_skips_validation(self) -> None:
        note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="unknown_synth")
        note.validate_range()  # Should not raise for unknown instruments


class TestTiming:
    def test_beats_to_ticks_default_ppq(self) -> None:
        assert beats_to_ticks(1.0) == 220
        assert beats_to_ticks(0.5) == 110

    def test_ticks_to_beats_default_ppq(self) -> None:
        assert ticks_to_beats(220) == 1.0
        assert ticks_to_beats(110) == 0.5

    def test_round_trip(self) -> None:
        original = 3.75
        ticks = beats_to_ticks(original)
        recovered = ticks_to_beats(ticks)
        assert abs(original - recovered) < 0.01

    def test_beats_to_seconds(self) -> None:
        assert beats_to_seconds(1.0, 120.0) == 0.5
        assert beats_to_seconds(4.0, 60.0) == 4.0

    def test_bars_to_beats_4_4(self) -> None:
        assert bars_to_beats(1, "4/4") == 4.0
        assert bars_to_beats(2, "4/4") == 8.0

    def test_bars_to_beats_3_4(self) -> None:
        assert bars_to_beats(1, "3/4") == 3.0

    def test_bars_to_beats_6_8(self) -> None:
        assert bars_to_beats(1, "6/8") == 3.0

    def test_invalid_time_signature(self) -> None:
        with pytest.raises(SpecValidationError):
            bars_to_beats(1, "invalid")


class TestNotation:
    def test_c4_to_midi(self) -> None:
        assert note_name_to_midi("C4") == 60

    def test_a4_to_midi(self) -> None:
        assert note_name_to_midi("A4") == 69

    def test_midi_to_c4(self) -> None:
        assert midi_to_note_name(60) == "C4"

    def test_midi_to_a4(self) -> None:
        assert midi_to_note_name(69) == "A4"

    def test_round_trip(self) -> None:
        for midi in [36, 48, 60, 72, 84, 96]:
            name = midi_to_note_name(midi)
            assert note_name_to_midi(name) == midi

    def test_sharp_notes(self) -> None:
        assert note_name_to_midi("F#3") == 54
        assert note_name_to_midi("C#5") == 73

    def test_flat_to_sharp_conversion(self) -> None:
        assert note_name_to_midi("Bb4") == note_name_to_midi("A#4")
        assert note_name_to_midi("Eb4") == note_name_to_midi("D#4")

    def test_invalid_note_name(self) -> None:
        with pytest.raises(SpecValidationError):
            note_name_to_midi("X4")

    def test_midi_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError):
            midi_to_note_name(200)

    def test_parse_key(self) -> None:
        root, scale = parse_key("C major")
        assert root == "C"
        assert scale == "major"

    def test_parse_key_with_sharp(self) -> None:
        root, scale = parse_key("F# minor")
        assert root == "F#"
        assert scale == "minor"

    def test_scale_notes_c_major(self) -> None:
        notes = scale_notes("C", "major", 4)
        assert notes[0] == 60  # C4
        assert len(notes) == 7


class TestScoreIR:
    def test_all_notes_sorted(self, sample_score_ir: ScoreIR) -> None:
        notes = sample_score_ir.all_notes()
        assert len(notes) == 8
        for i in range(len(notes) - 1):
            assert notes[i].start_beat <= notes[i + 1].start_beat

    def test_instruments(self, sample_score_ir: ScoreIR) -> None:
        assert sample_score_ir.instruments() == ["piano"]

    def test_total_bars(self, sample_score_ir: ScoreIR) -> None:
        assert sample_score_ir.total_bars() == 2

    def test_duration_seconds(self, sample_score_ir: ScoreIR) -> None:
        # 2 bars * 4 beats/bar = 8 beats, at 120 BPM = 4 seconds
        assert abs(sample_score_ir.duration_seconds() - 4.0) < 0.01

    def test_part_for_instrument(self, sample_score_ir: ScoreIR) -> None:
        notes = sample_score_ir.part_for_instrument("piano")
        assert len(notes) == 8
        assert all(n.instrument == "piano" for n in notes)

    def test_part_for_nonexistent_instrument(self, sample_score_ir: ScoreIR) -> None:
        notes = sample_score_ir.part_for_instrument("violin")
        assert notes == []

    def test_score_ir_is_frozen(self, sample_score_ir: ScoreIR) -> None:
        with pytest.raises(AttributeError):
            sample_score_ir.title = "Modified"  # type: ignore[misc]
