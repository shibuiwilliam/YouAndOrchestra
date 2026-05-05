"""Tests for B4 RhythmSystem Protocol and implementations."""

from __future__ import annotations

import pytest

from yao.ir.rhythm_system import (
    IqaSystem,
    RhythmSystem,
    TalaSystem,
    WesternMeter,
)


class TestRhythmSystemProtocol:
    """All implementations must satisfy the RhythmSystem Protocol."""

    def test_western_is_rhythm_system(self) -> None:
        assert isinstance(WesternMeter(), RhythmSystem)

    def test_tala_is_rhythm_system(self) -> None:
        assert isinstance(TalaSystem("tintal"), RhythmSystem)

    def test_iqa_is_rhythm_system(self) -> None:
        assert isinstance(IqaSystem("maqsoum"), RhythmSystem)


class TestWesternMeter:
    """Tests for WesternMeter."""

    def test_4_4_name(self) -> None:
        sys = WesternMeter(4, 4)
        assert "4/4" in sys.name

    def test_4_4_cycle_length(self) -> None:
        assert WesternMeter(4, 4).cycle_length() == 4

    def test_3_4_cycle_length(self) -> None:
        assert WesternMeter(3, 4).cycle_length() == 3

    def test_7_8_cycle_length(self) -> None:
        assert WesternMeter(7, 8).cycle_length() == 7

    def test_accent_length_matches_cycle(self) -> None:
        for n in [3, 4, 5, 6, 7]:
            sys = WesternMeter(n, 4)
            assert len(sys.accent_pattern()) == sys.cycle_length()

    def test_downbeat_strongest(self) -> None:
        sys = WesternMeter(4, 4)
        pattern = sys.accent_pattern()
        assert pattern[0] == 1.0
        assert all(p <= 1.0 for p in pattern)

    def test_6_8_compound_duple(self) -> None:
        sys = WesternMeter(6, 8)
        pattern = sys.accent_pattern()
        assert pattern[0] == 1.0  # beat 1
        assert pattern[3] == 0.7  # beat 4 (secondary strong)


class TestTalaSystem:
    """Tests for Indian tala system."""

    def test_tintal_16_beats(self) -> None:
        sys = TalaSystem("tintal")
        assert sys.cycle_length() == 16

    def test_jhaptal_10_beats(self) -> None:
        sys = TalaSystem("jhaptal")
        assert sys.cycle_length() == 10

    def test_rupak_7_beats(self) -> None:
        sys = TalaSystem("rupak")
        assert sys.cycle_length() == 7

    def test_accent_length_matches_cycle(self) -> None:
        for tala in ["tintal", "jhaptal", "rupak", "ektal"]:
            sys = TalaSystem(tala)
            assert len(sys.accent_pattern()) == sys.cycle_length()

    def test_sam_is_strongest(self) -> None:
        """Sam (first beat) should be the strongest accent."""
        sys = TalaSystem("tintal")
        pattern = sys.accent_pattern()
        assert pattern[0] == 1.0
        assert pattern[0] >= max(pattern[1:])

    def test_name_includes_tala(self) -> None:
        sys = TalaSystem("tintal")
        assert "tintal" in sys.name

    def test_unknown_tala_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown tala"):
            TalaSystem("invented")


class TestIqaSystem:
    """Tests for Arabic iqa system."""

    def test_maqsoum_8_beats(self) -> None:
        sys = IqaSystem("maqsoum")
        assert sys.cycle_length() == 8

    def test_baladi_4_beats(self) -> None:
        sys = IqaSystem("baladi")
        assert sys.cycle_length() == 4

    def test_accent_length_matches_cycle(self) -> None:
        for iqa in ["maqsoum", "masmoudi_kabir", "baladi", "saidi", "wahda"]:
            sys = IqaSystem(iqa)
            assert len(sys.accent_pattern()) == sys.cycle_length()

    def test_dum_is_strongest(self) -> None:
        """First dum stroke should be the strongest accent."""
        sys = IqaSystem("maqsoum")
        pattern = sys.accent_pattern()
        assert pattern[0] == 1.0

    def test_name_includes_iqa(self) -> None:
        sys = IqaSystem("maqsoum")
        assert "maqsoum" in sys.name

    def test_unknown_iqa_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown iqa"):
            IqaSystem("invented")

    def test_masmoudi_double_dum(self) -> None:
        """Masmoudi kabir has two dum strokes at beats 0 and 2."""
        sys = IqaSystem("masmoudi_kabir")
        pattern = sys.accent_pattern()
        assert pattern[0] == 1.0
        assert pattern[2] == 1.0
