"""Tests for extended instrument ranges added in v2.1."""

from __future__ import annotations

import pytest

from yao.constants.instruments import INSTRUMENT_RANGES, InstrumentRange

# All instruments added in the v2.1 extension
_EXTENDED_INSTRUMENTS = [
    # Guitar family
    "electric_guitar_muted",
    "electric_guitar_overdrive",
    "electric_guitar_distorted",
    "electric_guitar_harmonics",
    # Keyboard family
    "electric_piano_rhodes",
    "electric_piano_wurli",
    "clavinet",
    "hammond_organ",
    "rock_organ",
    # Bass family
    "upright_bass",
    "fretless_bass",
    "slap_bass",
    "synth_bass_sub",
    "synth_bass_acid",
    # Synth
    "pluck_synth",
]


@pytest.mark.parametrize("name", _EXTENDED_INSTRUMENTS)
def test_instrument_exists_in_registry(name: str) -> None:
    """Each extended instrument is present in INSTRUMENT_RANGES."""
    assert name in INSTRUMENT_RANGES, f"'{name}' missing from INSTRUMENT_RANGES"


@pytest.mark.parametrize("name", _EXTENDED_INSTRUMENTS)
def test_instrument_range_valid(name: str) -> None:
    """Each instrument has midi_low <= midi_high."""
    inst = INSTRUMENT_RANGES[name]
    assert isinstance(inst, InstrumentRange)
    assert inst.midi_low <= inst.midi_high, f"{name}: midi_low ({inst.midi_low}) > midi_high ({inst.midi_high})"


@pytest.mark.parametrize("name", _EXTENDED_INSTRUMENTS)
def test_instrument_has_family(name: str) -> None:
    """Each instrument has a non-empty family."""
    inst = INSTRUMENT_RANGES[name]
    assert inst.family, f"{name} has empty family"


@pytest.mark.parametrize("name", _EXTENDED_INSTRUMENTS)
def test_instrument_name_matches_key(name: str) -> None:
    """The .name field matches the dict key."""
    inst = INSTRUMENT_RANGES[name]
    assert inst.name == name
