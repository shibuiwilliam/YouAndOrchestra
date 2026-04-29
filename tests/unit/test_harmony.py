"""Tests for the harmony IR module."""

from __future__ import annotations

import pytest

from yao.errors import SpecValidationError
from yao.ir.harmony import (
    ChordFunction,
    diatonic_quality,
    make_progression,
    realize,
)


class TestChordFunction:
    def test_roman_numeral_major(self) -> None:
        assert ChordFunction(degree=0, quality="maj").roman == "I"
        assert ChordFunction(degree=3, quality="maj").roman == "IV"
        assert ChordFunction(degree=4, quality="maj").roman == "V"

    def test_roman_numeral_minor(self) -> None:
        assert ChordFunction(degree=1, quality="min").roman == "ii"
        assert ChordFunction(degree=5, quality="min").roman == "vi"

    def test_roman_numeral_diminished(self) -> None:
        assert ChordFunction(degree=6, quality="dim").roman == "vii°"

    def test_roman_numeral_dominant_seventh(self) -> None:
        assert ChordFunction(degree=4, quality="dom7").roman == "V7"

    def test_roman_numeral_secondary_dominant(self) -> None:
        cf = ChordFunction(degree=4, quality="dom7", applied_to=4)
        assert cf.roman == "V7/V"

    def test_frozen(self) -> None:
        cf = ChordFunction(degree=0, quality="maj")
        with pytest.raises(AttributeError):
            cf.degree = 1  # type: ignore[misc]


class TestDiatonicQuality:
    def test_major_scale_qualities(self) -> None:
        assert diatonic_quality(0, "major") == "maj"
        assert diatonic_quality(1, "major") == "min"
        assert diatonic_quality(2, "major") == "min"
        assert diatonic_quality(3, "major") == "maj"
        assert diatonic_quality(4, "major") == "maj"
        assert diatonic_quality(5, "major") == "min"
        assert diatonic_quality(6, "major") == "dim"

    def test_minor_scale_qualities(self) -> None:
        assert diatonic_quality(0, "minor") == "min"
        assert diatonic_quality(2, "minor") == "maj"

    def test_invalid_degree(self) -> None:
        with pytest.raises(SpecValidationError):
            diatonic_quality(7, "major")


class TestRealize:
    def test_c_major_triad(self) -> None:
        cf = ChordFunction(degree=0, quality="maj")
        pitches = realize(cf, "C", "major", 4)
        assert pitches == [60, 64, 67]  # C4, E4, G4

    def test_g_major_triad(self) -> None:
        cf = ChordFunction(degree=4, quality="maj")
        pitches = realize(cf, "C", "major", 4)
        assert pitches == [67, 71, 74]  # G4, B4, D5

    def test_first_inversion(self) -> None:
        cf = ChordFunction(degree=0, quality="maj", inversion=1)
        pitches = realize(cf, "C", "major", 4)
        # C goes up an octave: E4, G4, C5
        assert pitches == [64, 67, 72]

    def test_invalid_quality(self) -> None:
        cf = ChordFunction(degree=0, quality="invalid")
        with pytest.raises(SpecValidationError):
            realize(cf, "C", "major")


class TestChordProgression:
    def test_make_progression(self) -> None:
        prog = make_progression([0, 3, 4, 0], "C", "major")
        assert len(prog) == 4
        numerals = prog.roman_numerals()
        assert numerals == ["I", "IV", "V", "I"]

    def test_minor_progression(self) -> None:
        prog = make_progression([0, 3, 4, 0], "A", "minor")
        numerals = prog.roman_numerals()
        assert numerals == ["i", "iv", "v", "i"]
