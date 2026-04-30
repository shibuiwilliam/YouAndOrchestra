"""Music theory constants — scales, chords, note names, section types.

These are reference data, not aesthetic judgments. Adding a new scale or chord
type here is safe; changing the semantics of existing entries requires a
design review (CLAUDE.md §14).
"""

from __future__ import annotations

NOTE_NAMES: list[str] = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]
"""Chromatic note names using sharps. Index corresponds to pitch class (C=0)."""

ENHARMONIC_MAP: dict[str, str] = {
    "Db": "C#",
    "Eb": "D#",
    "Fb": "E",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
    "Cb": "B",
    "E#": "F",
    "B#": "C",
}
"""Maps flat/enharmonic note names to their canonical sharp equivalents."""

SCALE_INTERVALS: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "melodic_minor": (0, 2, 3, 5, 7, 9, 11),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
    "pentatonic_minor": (0, 3, 5, 7, 10),
    "blues": (0, 3, 5, 6, 7, 10),
    "whole_tone": (0, 2, 4, 6, 8, 10),
    "chromatic": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
}
"""Scale types mapped to their semitone intervals from the root."""

CHORD_INTERVALS: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "maj7": (0, 4, 7, 11),
    "min7": (0, 3, 7, 10),
    "dom7": (0, 4, 7, 10),
    "dim7": (0, 3, 6, 9),
    "half_dim7": (0, 3, 6, 10),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "add9": (0, 4, 7, 14),
    "min9": (0, 3, 7, 10, 14),
    "maj9": (0, 4, 7, 11, 14),
}
"""Chord types mapped to their semitone intervals from the root."""

SECTION_TYPES: list[str] = [
    "intro",
    "verse",
    "pre_chorus",
    "chorus",
    "bridge",
    "solo",
    "interlude",
    "breakdown",
    "build",
    "drop",
    "outro",
    "coda",
]
"""Recognized musical section types."""

DYNAMICS_TO_VELOCITY: dict[str, int] = {
    "ppp": 16,
    "pp": 33,
    "p": 49,
    "mp": 64,
    "mf": 80,
    "f": 96,
    "ff": 112,
    "fff": 127,
}
"""Standard dynamic markings mapped to approximate MIDI velocity values."""


TENSION_TO_DYNAMICS: list[tuple[float, str]] = [
    (0.15, "pp"),
    (0.30, "p"),
    (0.45, "mp"),
    (0.60, "mf"),
    (0.75, "f"),
    (0.90, "ff"),
]
"""Tension thresholds mapped to dynamics markings.

Each entry is (upper_bound, dynamics). Tension >= 0.9 maps to "fff".
Used by note realizers to convert trajectory tension to dynamic markings.
"""


def tension_to_dynamics(tension: float) -> str:
    """Map a tension value [0, 1] to a dynamics marking.

    Args:
        tension: Tension value between 0.0 and 1.0.

    Returns:
        A dynamics marking string (e.g., "mp", "f").
    """
    for threshold, dynamics in TENSION_TO_DYNAMICS:
        if tension < threshold:
            return dynamics
    return "fff"
