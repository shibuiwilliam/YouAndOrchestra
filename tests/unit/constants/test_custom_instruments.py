"""Tests for custom instrument profiles (Phase γ.7).

Tests cover:
- All 8 profiles load correctly
- All have valid MIDI ranges
- All non-Western instruments have cultural_origin
- All have idiomatic_techniques
- Discovery function works
"""

from __future__ import annotations

import pytest

from yao.constants.custom_instruments import (
    available_custom_instruments,
    load_custom_instrument,
)


class TestCustomInstruments:
    """Tests for custom instrument loading and validation."""

    def test_available_instruments_count(self) -> None:
        instruments = available_custom_instruments()
        assert len(instruments) >= 8

    def test_load_all_instruments(self) -> None:
        for name in available_custom_instruments():
            instr = load_custom_instrument(name)
            assert instr.name == name

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_custom_instrument("nonexistent_xyz")

    def test_all_have_valid_midi_range(self) -> None:
        for name in available_custom_instruments():
            instr = load_custom_instrument(name)
            assert 0 <= instr.midi_low < instr.midi_high <= 127, (
                f"{name}: invalid range [{instr.midi_low}, {instr.midi_high}]"
            )

    def test_all_have_cultural_origin(self) -> None:
        for name in available_custom_instruments():
            instr = load_custom_instrument(name)
            assert instr.cultural_origin, f"{name} missing cultural_origin"

    def test_all_have_techniques(self) -> None:
        for name in available_custom_instruments():
            instr = load_custom_instrument(name)
            assert len(instr.idiomatic_techniques) >= 3, f"{name} has only {len(instr.idiomatic_techniques)} techniques"

    def test_shakuhachi_is_japanese(self) -> None:
        shaku = load_custom_instrument("shakuhachi")
        assert shaku.cultural_origin == "japanese"
        assert shaku.gm_program == 77

    def test_oud_is_middle_eastern(self) -> None:
        oud = load_custom_instrument("oud")
        assert oud.cultural_origin == "middle_eastern"

    def test_sitar_is_indian(self) -> None:
        sitar = load_custom_instrument("sitar")
        assert sitar.cultural_origin == "indian"

    def test_koto_has_typical_scales(self) -> None:
        koto = load_custom_instrument("koto")
        assert "hirajoshi" in koto.typical_scales

    def test_velocity_range_valid(self) -> None:
        for name in available_custom_instruments():
            instr = load_custom_instrument(name)
            lo, hi = instr.typical_velocity_range
            assert 0 <= lo < hi <= 127, f"{name}: invalid velocity range [{lo}, {hi}]"
