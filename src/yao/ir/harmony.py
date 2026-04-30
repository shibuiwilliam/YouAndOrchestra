"""Chord progression representation using Roman numeral (functional) notation.

CLAUDE.md §7 mandates: "Chord function notation must use Roman numerals
(I, ii, V7/V etc.). Concrete chords are realized via yao.ir.harmony.realize().
Do not mix functional and concrete representations."
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.constants.music import CHORD_INTERVALS, SCALE_INTERVALS
from yao.errors import SpecValidationError
from yao.ir.notation import note_name_to_midi
from yao.types import MidiNote

# Diatonic chord quality per scale degree (0-indexed) for major and minor keys
_MAJOR_DIATONIC_QUALITY: dict[int, str] = {
    0: "maj",  # I
    1: "min",  # ii
    2: "min",  # iii
    3: "maj",  # IV
    4: "maj",  # V
    5: "min",  # vi
    6: "dim",  # vii°
}

_MINOR_DIATONIC_QUALITY: dict[int, str] = {
    0: "min",  # i
    1: "dim",  # ii°
    2: "maj",  # III
    3: "min",  # iv
    4: "min",  # v (natural minor; harmonic minor uses V major)
    5: "maj",  # VI
    6: "maj",  # VII (natural minor)
}

# Roman numeral labels
_ROMAN_NUMERALS: list[str] = ["I", "II", "III", "IV", "V", "VI", "VII"]


@dataclass(frozen=True)
class ChordFunction:
    """A chord described by its function within a key.

    Attributes:
        degree: Scale degree (0-indexed, 0=tonic through 6=leading tone).
        quality: Chord quality (maj, min, dim, aug, dom7, maj7, min7, etc.).
        inversion: Inversion number (0=root position, 1=first, 2=second).
        applied_to: If this is a secondary dominant, the target degree.
            e.g., V/V has applied_to=4 (targeting degree 4=V).
    """

    degree: int
    quality: str
    inversion: int = 0
    applied_to: int | None = None

    @property
    def roman(self) -> str:
        """Return the Roman numeral representation.

        Returns:
            String like "I", "ii", "V7/V", "vii°".
        """
        numeral = _ROMAN_NUMERALS[self.degree % 7]
        is_minor_quality = self.quality in ("min", "min7", "dim", "half_dim7")

        if is_minor_quality:
            numeral = numeral.lower()

        suffix = ""
        if self.quality == "dom7":
            suffix = "7"
        elif self.quality == "maj7":
            suffix = "maj7"
        elif self.quality == "min7":
            suffix = "7"
        elif self.quality == "dim":
            suffix = "°"
        elif self.quality == "dim7":
            suffix = "°7"
        elif self.quality == "half_dim7":
            suffix = "ø7"
        elif self.quality == "aug":
            suffix = "+"

        result = f"{numeral}{suffix}"

        if self.applied_to is not None:
            target = _ROMAN_NUMERALS[self.applied_to % 7]
            result = f"{result}/{target}"

        return result


@dataclass(frozen=True)
class ChordProgression:
    """An ordered sequence of chord functions within a key context.

    Attributes:
        chords: Immutable tuple of ChordFunction objects.
        key_root: Root note of the key (e.g., "C", "F#").
        scale_type: Scale type (e.g., "major", "minor").
    """

    chords: tuple[ChordFunction, ...]
    key_root: str
    scale_type: str

    def roman_numerals(self) -> list[str]:
        """Return the progression as a list of Roman numeral strings.

        Returns:
            List of strings like ["I", "IV", "V", "I"].
        """
        return [c.roman for c in self.chords]

    def __len__(self) -> int:
        return len(self.chords)


def diatonic_quality(degree: int, scale_type: str) -> str:
    """Determine the diatonic chord quality for a given scale degree.

    Args:
        degree: Scale degree (0-indexed).
        scale_type: Scale type (e.g., "major", "minor").

    Returns:
        Chord quality string (e.g., "maj", "min", "dim").

    Raises:
        SpecValidationError: If degree is out of range.
    """
    if not 0 <= degree <= 6:
        raise SpecValidationError(
            f"Scale degree must be 0–6, got {degree}.",
            field="degree",
        )

    if scale_type in ("minor", "harmonic_minor", "melodic_minor"):
        return _MINOR_DIATONIC_QUALITY[degree]
    return _MAJOR_DIATONIC_QUALITY[degree]


def realize(
    chord: ChordFunction,
    key_root: str,
    scale_type: str,
    octave: int = 4,
) -> list[MidiNote]:
    """Convert a functional chord to concrete MIDI pitches.

    Args:
        chord: The chord function to realize.
        key_root: Root note of the key (e.g., "C").
        scale_type: Scale type (e.g., "major", "minor").
        octave: Octave for the chord root.

    Returns:
        List of MIDI note numbers forming the chord.

    Raises:
        SpecValidationError: If chord quality or key is invalid.
    """
    if scale_type not in SCALE_INTERVALS:
        raise SpecValidationError(
            f"Unknown scale type '{scale_type}'.",
            field="scale_type",
        )
    if chord.quality not in CHORD_INTERVALS:
        raise SpecValidationError(
            f"Unknown chord quality '{chord.quality}'.",
            field="quality",
        )

    # Find the root pitch for this chord's scale degree
    scale = SCALE_INTERVALS[scale_type]
    degree_interval = scale[chord.degree % len(scale)]

    root_midi = note_name_to_midi(f"{key_root}{octave}")
    chord_root = root_midi + degree_interval

    # Build the chord from intervals
    intervals = CHORD_INTERVALS[chord.quality]
    pitches = [chord_root + interval for interval in intervals]

    # Apply inversion by moving lower notes up an octave
    for i in range(min(chord.inversion, len(pitches) - 1)):
        pitches[i] += 12

    pitches.sort()
    return pitches


def make_progression(
    degrees: list[int],
    key_root: str,
    scale_type: str,
) -> ChordProgression:
    """Create a chord progression from scale degrees with diatonic qualities.

    Args:
        degrees: List of scale degrees (0-indexed).
        key_root: Root note of the key.
        scale_type: Scale type.

    Returns:
        ChordProgression with diatonic qualities assigned.
    """
    chords = tuple(ChordFunction(degree=d, quality=diatonic_quality(d, scale_type)) for d in degrees)
    return ChordProgression(
        chords=chords,
        key_root=key_root,
        scale_type=scale_type,
    )
