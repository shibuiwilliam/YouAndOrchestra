"""Tests for extended time signature schema."""

from __future__ import annotations

import pytest

from yao.errors import SpecValidationError
from yao.schema.time_signature import PolymeterTrack, TimeSignatureSpec


class TestTimeSignatureSpecParsing:
    def test_simple_4_4(self) -> None:
        ts = TimeSignatureSpec(primary="4/4")
        assert ts.numerator() == 4
        assert ts.denominator() == 4

    def test_7_8_with_groupings(self) -> None:
        ts = TimeSignatureSpec(primary="7/8", beat_groupings=[3, 2, 2])
        assert ts.numerator() == 7
        assert ts.get_beat_grouping() == [3, 2, 2]

    def test_compound_6_8_auto_detected(self) -> None:
        ts = TimeSignatureSpec(primary="6/8")
        assert ts.is_compound()
        assert ts.get_beat_grouping() == [3, 3]

    def test_3_4_not_compound(self) -> None:
        ts = TimeSignatureSpec(primary="3/4")
        assert not ts.is_compound()

    def test_9_8_compound(self) -> None:
        ts = TimeSignatureSpec(primary="9/8")
        assert ts.is_compound()
        assert ts.get_beat_grouping() == [3, 3, 3]


class TestTimeSignatureValidation:
    def test_groupings_must_sum_to_numerator(self) -> None:
        with pytest.raises(SpecValidationError, match="sum to"):
            TimeSignatureSpec(primary="7/8", beat_groupings=[3, 3, 2])

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(SpecValidationError):
            TimeSignatureSpec(primary="invalid")


class TestPolymeter:
    def test_polymeter_with_sync_at(self) -> None:
        ts = TimeSignatureSpec(
            primary="4/4",
            polymeter=[
                PolymeterTrack(instrument="piano", time_signature="4/4", sync_at=4),
                PolymeterTrack(instrument="drums", time_signature="7/8", sync_at=4),
            ],
        )
        assert ts.polymeter is not None
        assert len(ts.polymeter) == 2

    def test_polymeter_without_positive_sync_raises(self) -> None:
        with pytest.raises(SpecValidationError, match="sync_at"):
            PolymeterTrack(instrument="piano", time_signature="4/4", sync_at=0)
