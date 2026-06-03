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
    "electric_piano_rhodes": InstrumentRange("electric_piano_rhodes", 28, 103, 4, "keyboard"),
    "electric_piano_wurli": InstrumentRange("electric_piano_wurli", 28, 103, 5, "keyboard"),
    "harpsichord": InstrumentRange("harpsichord", 29, 89, 6, "keyboard"),
    "clavinet": InstrumentRange("clavinet", 36, 84, 7, "keyboard"),
    "celesta": InstrumentRange("celesta", 60, 108, 8, "keyboard"),
    "organ": InstrumentRange("organ", 36, 96, 19, "keyboard"),
    "hammond_organ": InstrumentRange("hammond_organ", 36, 96, 16, "keyboard"),
    "rock_organ": InstrumentRange("rock_organ", 36, 96, 18, "keyboard"),
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
    "electric_guitar_muted": InstrumentRange("electric_guitar_muted", 40, 88, 28, "guitar"),
    "electric_guitar_overdrive": InstrumentRange("electric_guitar_overdrive", 40, 88, 29, "guitar"),
    "electric_guitar_distorted": InstrumentRange("electric_guitar_distorted", 40, 88, 30, "guitar"),
    "electric_guitar_harmonics": InstrumentRange("electric_guitar_harmonics", 40, 88, 31, "guitar"),
    # Bass
    "upright_bass": InstrumentRange("upright_bass", 28, 60, 32, "bass"),
    "acoustic_bass": InstrumentRange("acoustic_bass", 28, 60, 32, "bass"),
    "electric_bass_finger": InstrumentRange("electric_bass_finger", 28, 65, 33, "bass"),
    "electric_bass_pick": InstrumentRange("electric_bass_pick", 28, 65, 34, "bass"),
    "fretless_bass": InstrumentRange("fretless_bass", 28, 65, 35, "bass"),
    "slap_bass": InstrumentRange("slap_bass", 28, 65, 36, "bass"),
    "synth_bass": InstrumentRange("synth_bass", 24, 72, 38, "bass"),
    "synth_bass_sub": InstrumentRange("synth_bass_sub", 24, 60, 38, "bass"),
    "synth_bass_acid": InstrumentRange("synth_bass_acid", 24, 72, 39, "bass"),
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
    # Synth — Plucked (GM program 84)
    "pluck_synth": InstrumentRange("pluck_synth", 36, 96, 84, "synth"),
    # Synth — Leads (GM programs 80-87)
    "synth_lead_square": InstrumentRange("synth_lead_square", 24, 108, 80, "synth"),
    "synth_lead_saw": InstrumentRange("synth_lead_saw", 24, 108, 81, "synth"),
    "synth_lead_calliope": InstrumentRange("synth_lead_calliope", 24, 108, 82, "synth"),
    "synth_lead_chiff": InstrumentRange("synth_lead_chiff", 24, 108, 83, "synth"),
    "synth_lead_charang": InstrumentRange("synth_lead_charang", 24, 108, 84, "synth"),
    "synth_lead_voice": InstrumentRange("synth_lead_voice", 24, 108, 85, "synth"),
    "synth_lead_fifths": InstrumentRange("synth_lead_fifths", 24, 108, 86, "synth"),
    "synth_lead_bass_lead": InstrumentRange("synth_lead_bass_lead", 24, 108, 87, "synth"),
    # Synth — Pads (GM programs 88-95)
    "synth_pad_new_age": InstrumentRange("synth_pad_new_age", 24, 108, 88, "synth"),
    "synth_pad_warm": InstrumentRange("synth_pad_warm", 24, 108, 89, "synth"),
    "synth_pad_polysynth": InstrumentRange("synth_pad_polysynth", 24, 108, 90, "synth"),
    "synth_pad_choir": InstrumentRange("synth_pad_choir", 24, 108, 91, "synth"),
    "synth_pad_bowed": InstrumentRange("synth_pad_bowed", 24, 108, 92, "synth"),
    "synth_pad_metallic": InstrumentRange("synth_pad_metallic", 24, 108, 93, "synth"),
    "synth_pad_halo": InstrumentRange("synth_pad_halo", 24, 108, 94, "synth"),
    "synth_pad_sweep": InstrumentRange("synth_pad_sweep", 24, 108, 95, "synth"),
    # Synth — Effects (GM programs 96-103)
    "synth_fx_rain": InstrumentRange("synth_fx_rain", 24, 108, 96, "synth"),
    "synth_fx_soundtrack": InstrumentRange("synth_fx_soundtrack", 24, 108, 97, "synth"),
    "synth_fx_crystal": InstrumentRange("synth_fx_crystal", 24, 108, 98, "synth"),
    "synth_fx_atmosphere": InstrumentRange("synth_fx_atmosphere", 24, 108, 99, "synth"),
    "synth_fx_brightness": InstrumentRange("synth_fx_brightness", 24, 108, 100, "synth"),
    "synth_fx_goblins": InstrumentRange("synth_fx_goblins", 24, 108, 101, "synth"),
    "synth_fx_echoes": InstrumentRange("synth_fx_echoes", 24, 108, 102, "synth"),
    "synth_fx_sci_fi": InstrumentRange("synth_fx_sci_fi", 24, 108, 103, "synth"),
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
    # Chinese traditional
    "guzheng": InstrumentRange("guzheng", 48, 96, 107, "strings"),
    "erhu": InstrumentRange("erhu", 55, 86, 40, "strings"),
    "dizi": InstrumentRange("dizi", 62, 86, 73, "woodwind"),
    "pipa": InstrumentRange("pipa", 45, 76, 104, "strings"),
    "bianzhong": InstrumentRange("bianzhong", 48, 84, 14, "percussion"),
}
"""All known instrument ranges. Key is the canonical instrument name."""
