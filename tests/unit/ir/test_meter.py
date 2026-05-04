"""Tests for MeterSpec IR."""

from __future__ import annotations

import pytest

from yao.errors import SpecValidationError
from yao.ir.meter import MeterSpec, parse_meter_string


class TestMeterSpecConstruction:
    """Test MeterSpec creation and basic properties."""

    def test_4_4_defaults(self) -> None:
        m = parse_meter_string("4/4")
        assert m.numerator == 4
        assert m.denominator == 4
        assert m.grouping == (1, 1, 1, 1)
        assert m.is_compound is False
        assert m.pulse_unit == 1.0
        assert m.beats_per_bar() == 4.0

    def test_3_4_waltz(self) -> None:
        m = parse_meter_string("3/4")
        assert m.numerator == 3
        assert m.denominator == 4
        assert m.grouping == (1, 1, 1)
        assert m.is_compound is False
        assert m.beats_per_bar() == 3.0

    def test_6_8_compound(self) -> None:
        m = parse_meter_string("6/8")
        assert m.is_compound is True
        assert m.grouping == (3, 3)
        assert m.pulse_unit == 1.5  # dotted quarter
        assert m.beats_per_bar() == 3.0
        assert m.group_count() == 2

    def test_9_8_compound(self) -> None:
        m = parse_meter_string("9/8")
        assert m.is_compound is True
        assert m.grouping == (3, 3, 3)
        assert m.beats_per_bar() == 4.5

    def test_12_8_compound(self) -> None:
        m = parse_meter_string("12/8")
        assert m.is_compound is True
        assert m.grouping == (3, 3, 3, 3)

    def test_5_4_default_grouping(self) -> None:
        m = parse_meter_string("5/4")
        assert m.numerator == 5
        assert m.grouping == (1, 1, 1, 1, 1)
        assert m.beats_per_bar() == 5.0

    def test_5_4_explicit_grouping(self) -> None:
        m = parse_meter_string("5/4", groupings=[3, 2])
        assert m.grouping == (3, 2)

    def test_7_8_bulgarian(self) -> None:
        m = parse_meter_string("7/8", groupings=[2, 2, 3])
        assert m.grouping == (2, 2, 3)
        assert m.is_compound is False
        assert m.beats_per_bar() == 3.5

    def test_7_8_bartok(self) -> None:
        m = parse_meter_string("7/8", groupings=[3, 2, 2])
        assert m.grouping == (3, 2, 2)

    def test_7_8_kalamatianos(self) -> None:
        m = parse_meter_string("7/8", groupings=[2, 3, 2])
        assert m.grouping == (2, 3, 2)

    def test_11_8_with_grouping(self) -> None:
        m = parse_meter_string("11/8", groupings=[3, 2, 3, 3])
        assert m.grouping == (3, 2, 3, 3)
        assert sum(m.grouping) == 11


class TestMeterSpecGroupDurations:
    """Test group_durations_beats() method."""

    def test_4_4_group_durations(self) -> None:
        m = parse_meter_string("4/4")
        assert m.group_durations_beats() == (1.0, 1.0, 1.0, 1.0)

    def test_6_8_group_durations(self) -> None:
        m = parse_meter_string("6/8")
        assert m.group_durations_beats() == (1.5, 1.5)

    def test_7_8_group_durations(self) -> None:
        m = parse_meter_string("7/8", groupings=[3, 2, 2])
        durations = m.group_durations_beats()
        assert abs(durations[0] - 1.5) < 0.001
        assert abs(durations[1] - 1.0) < 0.001
        assert abs(durations[2] - 1.0) < 0.001


class TestMeterSpecAccents:
    """Test metric accent generation."""

    def test_4_4_accents(self) -> None:
        m = parse_meter_string("4/4")
        assert m.metric_accents[0] == 1.0  # downbeat strongest
        assert len(m.metric_accents) == 4

    def test_6_8_accents(self) -> None:
        m = parse_meter_string("6/8")
        assert m.metric_accents[0] == 1.0
        assert len(m.metric_accents) == 2

    def test_downbeat_always_strongest(self) -> None:
        for ts in ["4/4", "3/4", "6/8", "5/4"]:
            m = parse_meter_string(ts)
            assert m.metric_accents[0] == 1.0, f"Downbeat not 1.0 for {ts}"
            for i, a in enumerate(m.metric_accents[1:], 1):
                assert a < 1.0, f"Non-downbeat accent >= 1.0 at position {i} for {ts}"


class TestMeterSpecValidation:
    """Test error handling."""

    def test_malformed_time_signature(self) -> None:
        with pytest.raises(SpecValidationError):
            parse_meter_string("not_a_meter")

    def test_grouping_sum_mismatch(self) -> None:
        with pytest.raises(SpecValidationError, match="sum to"):
            parse_meter_string("7/8", groupings=[3, 3, 3])

    def test_grouping_sum_too_small(self) -> None:
        with pytest.raises(SpecValidationError):
            parse_meter_string("7/8", groupings=[2, 2])


class TestMeterSpecFrozen:
    """Verify immutability."""

    def test_frozen(self) -> None:
        m = parse_meter_string("4/4")
        with pytest.raises(AttributeError):
            m.numerator = 3  # type: ignore[misc]

    def test_from_time_signature_classmethod(self) -> None:
        m = MeterSpec.from_time_signature("7/8", groupings=[2, 2, 3])
        assert m.numerator == 7


class TestDifferentGroupingsAreDifferent:
    """7/8 (2,2,3) != 7/8 (3,2,2) — grouping disambiguates feel."""

    def test_grouping_distinction(self) -> None:
        bulgarian = parse_meter_string("7/8", groupings=[2, 2, 3])
        bartok = parse_meter_string("7/8", groupings=[3, 2, 2])
        assert bulgarian.grouping != bartok.grouping
        assert bulgarian.numerator == bartok.numerator
