"""Tests for extended timing utilities — compound meter and beat grouping."""

from __future__ import annotations

from yao.ir.timing import (
    bars_to_beats,
    beat_grouping,
    beats_per_bar_from_sig,
    beats_to_bars,
    is_compound,
    parse_time_signature,
)


class TestParseTimeSignature:
    def test_4_4(self) -> None:
        assert parse_time_signature("4/4") == (4, 4)

    def test_7_8(self) -> None:
        assert parse_time_signature("7/8") == (7, 8)

    def test_6_8(self) -> None:
        assert parse_time_signature("6/8") == (6, 8)


class TestIsCompound:
    def test_6_8_is_compound(self) -> None:
        assert is_compound("6/8")

    def test_9_8_is_compound(self) -> None:
        assert is_compound("9/8")

    def test_12_8_is_compound(self) -> None:
        assert is_compound("12/8")

    def test_3_4_not_compound(self) -> None:
        assert not is_compound("3/4")

    def test_4_4_not_compound(self) -> None:
        assert not is_compound("4/4")

    def test_3_8_not_compound(self) -> None:
        # 3/8 has numerator 3, but exactly 3 is excluded (simple triple)
        assert not is_compound("3/8")


class TestBeatsPerBar:
    def test_4_4(self) -> None:
        assert beats_per_bar_from_sig(4, 4) == 4.0

    def test_3_4(self) -> None:
        assert beats_per_bar_from_sig(3, 4) == 3.0

    def test_6_8(self) -> None:
        assert beats_per_bar_from_sig(6, 8) == 3.0

    def test_7_8(self) -> None:
        assert beats_per_bar_from_sig(7, 8) == 3.5


class TestBeatGrouping:
    def test_7_8_explicit(self) -> None:
        groups = beat_grouping("7/8", [3, 2, 2])
        assert groups == [1.5, 1.0, 1.0]

    def test_6_8_auto_compound(self) -> None:
        groups = beat_grouping("6/8")
        assert groups == [1.5, 1.5]

    def test_4_4_auto_simple(self) -> None:
        groups = beat_grouping("4/4")
        assert groups == [1.0, 1.0, 1.0, 1.0]

    def test_5_8_explicit(self) -> None:
        groups = beat_grouping("5/8", [3, 2])
        assert groups == [1.5, 1.0]


class TestBarsToBeats:
    def test_backward_compat_4_4(self) -> None:
        assert bars_to_beats(4, "4/4") == 16.0

    def test_backward_compat_3_4(self) -> None:
        assert bars_to_beats(4, "3/4") == 12.0

    def test_7_8(self) -> None:
        assert bars_to_beats(2, "7/8") == 7.0

    def test_6_8(self) -> None:
        assert bars_to_beats(2, "6/8") == 6.0


class TestBeatsToBar:
    def test_4_4(self) -> None:
        assert beats_to_bars(16.0, "4/4") == 4.0

    def test_7_8(self) -> None:
        assert beats_to_bars(7.0, "7/8") == 2.0
