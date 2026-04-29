"""Note name and MIDI number conversions.

Uses scientific pitch notation: C4 = MIDI 60.
All note-name/MIDI conversions MUST go through this module (CLAUDE.md §7).
"""

from __future__ import annotations

import re

from yao.constants.music import ENHARMONIC_MAP, NOTE_NAMES, SCALE_INTERVALS
from yao.errors import SpecValidationError
from yao.types import MidiNote

_NOTE_PATTERN = re.compile(r"^([A-Ga-g][#b]?)(-?\d+)$")


def note_name_to_midi(name: str) -> MidiNote:
    """Convert a scientific pitch notation name to a MIDI note number.

    Args:
        name: Note name like "C4", "F#3", "Bb5".

    Returns:
        MIDI note number (e.g., 60 for C4).

    Raises:
        SpecValidationError: If the name is not a valid note.
    """
    match = _NOTE_PATTERN.match(name)
    if not match:
        raise SpecValidationError(
            f"Invalid note name '{name}'. Expected format like 'C4', 'F#3'.",
            field="note_name",
        )
    note_part = match.group(1)
    octave = int(match.group(2))

    # Normalize enharmonics
    note_upper = note_part[0].upper() + note_part[1:]
    if note_upper in ENHARMONIC_MAP:
        note_upper = ENHARMONIC_MAP[note_upper]

    if note_upper not in NOTE_NAMES:
        raise SpecValidationError(
            f"Unknown note '{note_upper}' in '{name}'.",
            field="note_name",
        )

    pitch_class = NOTE_NAMES.index(note_upper)
    midi = (octave + 1) * 12 + pitch_class
    if not 0 <= midi <= 127:
        raise SpecValidationError(
            f"Note '{name}' maps to MIDI {midi}, which is out of range (0–127).",
            field="note_name",
        )
    return midi


def midi_to_note_name(midi: MidiNote) -> str:
    """Convert a MIDI note number to scientific pitch notation.

    Args:
        midi: MIDI note number (0–127).

    Returns:
        Note name like "C4", "F#3".

    Raises:
        SpecValidationError: If midi is out of range.
    """
    if not 0 <= midi <= 127:
        raise SpecValidationError(
            f"MIDI note {midi} out of range (0–127).",
            field="midi_note",
        )
    octave = (midi // 12) - 1
    pitch_class = midi % 12
    return f"{NOTE_NAMES[pitch_class]}{octave}"


def parse_key(key: str) -> tuple[str, str]:
    """Parse a key string like 'C major' into (root_note, scale_type).

    Args:
        key: Key string, e.g., "C major", "F# minor", "Bb dorian".

    Returns:
        Tuple of (root_note, scale_type).

    Raises:
        SpecValidationError: If the key string is invalid.
    """
    parts = key.split()
    if len(parts) != 2:  # noqa: PLR2004
        raise SpecValidationError(
            f"Key must be 'Note Scale' (e.g., 'C major'), got '{key}'.",
            field="key",
        )
    root, scale_type = parts[0], parts[1]

    # Normalize root
    root_upper = root[0].upper() + root[1:] if len(root) > 1 else root.upper()
    if root_upper in ENHARMONIC_MAP:
        root_upper = ENHARMONIC_MAP[root_upper]
    if root_upper not in NOTE_NAMES:
        raise SpecValidationError(
            f"Unknown root note '{root}' in key '{key}'.",
            field="key",
        )
    if scale_type not in SCALE_INTERVALS:
        raise SpecValidationError(
            f"Unknown scale type '{scale_type}'. Valid: {list(SCALE_INTERVALS.keys())}.",
            field="key",
        )
    return root_upper, scale_type


def scale_notes(root: str, scale_type: str, octave: int = 4) -> list[MidiNote]:
    """Generate MIDI note numbers for a scale in a given octave.

    Args:
        root: Root note name (e.g., "C", "F#").
        scale_type: Scale type (e.g., "major", "minor").
        octave: Octave number (default 4).

    Returns:
        List of MIDI note numbers for the scale.

    Raises:
        SpecValidationError: If root or scale_type is invalid.
    """
    if root in ENHARMONIC_MAP:
        root = ENHARMONIC_MAP[root]
    if root not in NOTE_NAMES:
        raise SpecValidationError(f"Unknown root note '{root}'.", field="root")
    if scale_type not in SCALE_INTERVALS:
        raise SpecValidationError(f"Unknown scale type '{scale_type}'.", field="scale_type")

    root_midi = note_name_to_midi(f"{root}{octave}")
    intervals = SCALE_INTERVALS[scale_type]
    return [root_midi + interval for interval in intervals]
