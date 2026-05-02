"""Tests for the Tuning module — cents-based pitch conversion."""

from __future__ import annotations

from yao.constants.scales import MAJOR, MAQAM_RAST
from yao.ir.tuning import Tuning


class TestCentsFromA4:
    def test_a4_is_zero(self) -> None:
        assert Tuning.cents_from_a4(69) == 0.0

    def test_c4_is_negative_900(self) -> None:
        # C4 = MIDI 60, 9 semitones below A4
        assert Tuning.cents_from_a4(60) == -900.0

    def test_with_offset(self) -> None:
        assert Tuning.cents_from_a4(69, 50.0) == 50.0

    def test_c5_is_300(self) -> None:
        # C5 = MIDI 72 = 3 semitones above A4
        assert Tuning.cents_from_a4(72) == 300.0


class TestMidiFromCents:
    def test_zero_cents_is_a4(self) -> None:
        midi, bend = Tuning.midi_from_cents(0.0)
        assert midi == 69
        assert bend == 0.0

    def test_50_cents_above_a4(self) -> None:
        midi, bend = Tuning.midi_from_cents(50.0)
        # 50 cents is exactly between A4 and A#4; Python rounds to 70
        assert midi == 70
        assert abs(bend - (-50.0)) < 0.1

    def test_100_cents_is_a_sharp(self) -> None:
        midi, bend = Tuning.midi_from_cents(100.0)
        assert midi == 70  # A#4
        assert abs(bend) < 0.1

    def test_round_trip(self) -> None:
        for midi_in in [48, 60, 69, 72, 84]:
            cents = Tuning.cents_from_a4(midi_in)
            midi_out, bend = Tuning.midi_from_cents(cents)
            assert midi_out == midi_in
            assert abs(bend) < 0.1

    def test_clamped_to_valid_range(self) -> None:
        midi, _ = Tuning.midi_from_cents(-10000.0)
        assert midi >= 0
        midi, _ = Tuning.midi_from_cents(10000.0)
        assert midi <= 127


class TestPitchBendFromCents:
    def test_zero_cents_zero_bend(self) -> None:
        assert Tuning.pitch_bend_from_cents(0.0) == 0

    def test_100_cents_with_range_2(self) -> None:
        # 100 cents = half of 200 cent range → ~4096
        bend = Tuning.pitch_bend_from_cents(100.0, bend_range_semitones=2)
        assert 4000 < bend < 4200

    def test_negative_200_cents(self) -> None:
        bend = Tuning.pitch_bend_from_cents(-200.0, bend_range_semitones=2)
        assert bend == -8192

    def test_clamped(self) -> None:
        bend = Tuning.pitch_bend_from_cents(1000.0, bend_range_semitones=2)
        assert bend == 8191


class TestScalePitchesCents:
    def test_12edo_major_no_bend(self) -> None:
        pitches = Tuning.scale_pitches_cents(60, MAJOR)
        for _midi, bend in pitches:
            assert bend == 0.0

    def test_maqam_rast_has_quarter_tones(self) -> None:
        pitches = Tuning.scale_pitches_cents(60, MAQAM_RAST)
        bends = [bend for _, bend in pitches]
        # At least one pitch should have non-zero bend (quarter-tone)
        assert any(abs(b) > 1.0 for b in bends)

    def test_correct_degree_count(self) -> None:
        pitches = Tuning.scale_pitches_cents(60, MAJOR, octaves=1)
        assert len(pitches) == 7  # major has 7 degrees

    def test_two_octaves(self) -> None:
        pitches = Tuning.scale_pitches_cents(60, MAJOR, octaves=2)
        assert len(pitches) == 14


class TestPitchClassCents:
    def test_c4(self) -> None:
        # C = pitch class 0
        pc = Tuning.pitch_class_cents(60)
        assert pc == 0.0

    def test_a4(self) -> None:
        # A = pitch class 900 cents
        pc = Tuning.pitch_class_cents(69)
        assert pc == 900.0

    def test_with_offset(self) -> None:
        pc = Tuning.pitch_class_cents(60, 50.0)
        assert pc == 50.0
