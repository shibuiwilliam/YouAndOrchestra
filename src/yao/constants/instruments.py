"""Instrument range definitions.

All instrument ranges are centralized here. Code that validates note ranges
MUST reference these definitions — never hardcode ranges locally (CLAUDE.md §7).
Ranges use scientific pitch notation: C4 = MIDI 60.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentRange:
    """Physical playable range of an instrument.

    Attributes:
        name: Canonical instrument name.
        midi_low: Lowest playable MIDI note number.
        midi_high: Highest playable MIDI note number.
        program: General MIDI program number.
        family: Instrument family (keyboard, strings, brass, etc.).
    """

    name: str
    midi_low: int
    midi_high: int
    program: int
    family: str


INSTRUMENT_RANGES: dict[str, InstrumentRange] = {
    # Keyboard
    "piano": InstrumentRange("piano", 21, 108, 0, "keyboard"),
    "electric_piano": InstrumentRange("electric_piano", 28, 103, 4, "keyboard"),
    "harpsichord": InstrumentRange("harpsichord", 29, 89, 6, "keyboard"),
    "celesta": InstrumentRange("celesta", 60, 108, 8, "keyboard"),
    "organ": InstrumentRange("organ", 36, 96, 19, "keyboard"),
    # Strings
    "violin": InstrumentRange("violin", 55, 103, 40, "strings"),
    "viola": InstrumentRange("viola", 48, 93, 41, "strings"),
    "cello": InstrumentRange("cello", 36, 76, 42, "strings"),
    "contrabass": InstrumentRange("contrabass", 28, 60, 43, "strings"),
    "harp": InstrumentRange("harp", 24, 103, 46, "strings"),
    "strings_ensemble": InstrumentRange("strings_ensemble", 28, 103, 48, "strings"),
    # Guitar
    "acoustic_guitar_nylon": InstrumentRange("acoustic_guitar_nylon", 40, 84, 24, "guitar"),
    "acoustic_guitar_steel": InstrumentRange("acoustic_guitar_steel", 40, 84, 25, "guitar"),
    "electric_guitar_clean": InstrumentRange("electric_guitar_clean", 40, 88, 27, "guitar"),
    # Bass
    "acoustic_bass": InstrumentRange("acoustic_bass", 28, 60, 32, "bass"),
    "electric_bass_finger": InstrumentRange("electric_bass_finger", 28, 65, 33, "bass"),
    "electric_bass_pick": InstrumentRange("electric_bass_pick", 28, 65, 34, "bass"),
    "synth_bass": InstrumentRange("synth_bass", 24, 72, 38, "bass"),
    # Brass
    "trumpet": InstrumentRange("trumpet", 55, 82, 56, "brass"),
    "trombone": InstrumentRange("trombone", 40, 72, 57, "brass"),
    "tuba": InstrumentRange("tuba", 28, 58, 58, "brass"),
    "french_horn": InstrumentRange("french_horn", 34, 77, 60, "brass"),
    # Woodwind
    "oboe": InstrumentRange("oboe", 58, 91, 68, "woodwind"),
    "clarinet": InstrumentRange("clarinet", 50, 91, 71, "woodwind"),
    "flute": InstrumentRange("flute", 60, 96, 73, "woodwind"),
    "piccolo": InstrumentRange("piccolo", 74, 108, 72, "woodwind"),
    "bassoon": InstrumentRange("bassoon", 34, 75, 70, "woodwind"),
    # Saxophone
    "alto_sax": InstrumentRange("alto_sax", 49, 80, 65, "saxophone"),
    "tenor_sax": InstrumentRange("tenor_sax", 44, 75, 66, "saxophone"),
    "baritone_sax": InstrumentRange("baritone_sax", 36, 69, 67, "saxophone"),
    # Synth
    "synth_lead_square": InstrumentRange("synth_lead_square", 24, 108, 80, "synth"),
    "synth_lead_saw": InstrumentRange("synth_lead_saw", 24, 108, 81, "synth"),
    "synth_pad_warm": InstrumentRange("synth_pad_warm", 24, 108, 89, "synth"),
    # Percussion (pitched)
    "timpani": InstrumentRange("timpani", 40, 57, 47, "percussion"),
    "vibraphone": InstrumentRange("vibraphone", 53, 89, 11, "percussion"),
    "marimba": InstrumentRange("marimba", 45, 96, 12, "percussion"),
    "xylophone": InstrumentRange("xylophone", 65, 108, 13, "percussion"),
    "glockenspiel": InstrumentRange("glockenspiel", 72, 108, 9, "percussion"),
    # Non-Western / custom instruments
    "shakuhachi": InstrumentRange("shakuhachi", 55, 84, 77, "woodwind"),
    "koto": InstrumentRange("koto", 40, 84, 107, "strings"),
    "shamisen": InstrumentRange("shamisen", 50, 79, 106, "strings"),
    "taiko": InstrumentRange("taiko", 36, 60, 116, "percussion"),
    "sitar": InstrumentRange("sitar", 48, 84, 104, "strings"),
    "tabla": InstrumentRange("tabla", 36, 72, 115, "percussion"),
    "oud": InstrumentRange("oud", 43, 79, 25, "strings"),
    "ney": InstrumentRange("ney", 55, 86, 72, "woodwind"),
}
"""All known instrument ranges. Key is the canonical instrument name."""
