"""Centralized constants — instrument ranges, MIDI mappings, music theory."""

from __future__ import annotations

from yao.constants.instruments import INSTRUMENT_RANGES, InstrumentRange
from yao.constants.midi import (
    DEFAULT_BPM,
    DEFAULT_PPQ,
    DEFAULT_VELOCITY,
    GENERAL_MIDI_INSTRUMENTS,
    MIDI_NOTE_MAX,
    MIDI_NOTE_MIN,
)
from yao.constants.music import CHORD_INTERVALS, NOTE_NAMES, SCALE_INTERVALS, SECTION_TYPES

__all__ = [
    "CHORD_INTERVALS",
    "DEFAULT_BPM",
    "DEFAULT_PPQ",
    "DEFAULT_VELOCITY",
    "GENERAL_MIDI_INSTRUMENTS",
    "INSTRUMENT_RANGES",
    "InstrumentRange",
    "MIDI_NOTE_MAX",
    "MIDI_NOTE_MIN",
    "NOTE_NAMES",
    "SCALE_INTERVALS",
    "SECTION_TYPES",
]
