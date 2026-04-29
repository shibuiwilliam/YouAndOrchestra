"""MIDI-specific constants.

All MIDI magic numbers are centralized here.
Never hardcode MIDI program numbers, PPQ, or velocity values elsewhere.
"""

from __future__ import annotations

DEFAULT_PPQ: int = 220
"""Default pulses per quarter note (pretty_midi resolution)."""

DEFAULT_VELOCITY: int = 80
"""Default MIDI velocity when no dynamics curve is specified."""

DEFAULT_BPM: float = 120.0
"""Default tempo in beats per minute."""

MIDI_NOTE_MIN: int = 0
"""Lowest possible MIDI note number."""

MIDI_NOTE_MAX: int = 127
"""Highest possible MIDI note number."""

GENERAL_MIDI_INSTRUMENTS: dict[str, int] = {
    "piano": 0,
    "bright_piano": 1,
    "electric_piano": 4,
    "harpsichord": 6,
    "celesta": 8,
    "glockenspiel": 9,
    "music_box": 10,
    "vibraphone": 11,
    "marimba": 12,
    "xylophone": 13,
    "organ": 19,
    "acoustic_guitar_nylon": 24,
    "acoustic_guitar_steel": 25,
    "electric_guitar_clean": 27,
    "electric_guitar_distortion": 30,
    "acoustic_bass": 32,
    "electric_bass_finger": 33,
    "electric_bass_pick": 34,
    "slap_bass": 36,
    "synth_bass": 38,
    "violin": 40,
    "viola": 41,
    "cello": 42,
    "contrabass": 43,
    "tremolo_strings": 44,
    "pizzicato_strings": 45,
    "harp": 46,
    "timpani": 47,
    "strings_ensemble": 48,
    "synth_strings": 50,
    "choir_aahs": 52,
    "voice_oohs": 53,
    "trumpet": 56,
    "trombone": 57,
    "tuba": 58,
    "french_horn": 60,
    "brass_section": 61,
    "soprano_sax": 64,
    "alto_sax": 65,
    "tenor_sax": 66,
    "baritone_sax": 67,
    "oboe": 68,
    "english_horn": 69,
    "bassoon": 70,
    "clarinet": 71,
    "piccolo": 72,
    "flute": 73,
    "recorder": 74,
    "pan_flute": 75,
    "whistle": 78,
    "ocarina": 79,
    "synth_lead_square": 80,
    "synth_lead_saw": 81,
    "synth_pad_warm": 89,
    "synth_pad_strings": 91,
}
"""Mapping from instrument name to General MIDI program number."""
