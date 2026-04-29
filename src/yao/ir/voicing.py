"""Voice leading utilities — voicing representation and parallel motion detection.

CLAUDE.md §7: "Voicing checks go through yao.ir.voicing.
Parallel 5th/8ve detection uses yao.verify.voice_leading."

This module provides the IR-level voicing representation. The actual
voice leading *verification* rules live in verify/ (Layer 6), but the
data structures and basic interval computation are here in IR (Layer 1).
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.ir.harmony import ChordFunction
from yao.types import MidiNote


@dataclass(frozen=True)
class Voicing:
    """A specific pitch arrangement of a chord.

    Attributes:
        pitches: MIDI note numbers from lowest to highest.
        chord_function: The functional chord this voicing realizes (optional).
    """

    pitches: tuple[MidiNote, ...]
    chord_function: ChordFunction | None = None

    @property
    def voice_count(self) -> int:
        """Number of voices in this voicing."""
        return len(self.pitches)

    @property
    def span(self) -> int:
        """Total semitone span from lowest to highest pitch."""
        if len(self.pitches) < 2:  # noqa: PLR2004
            return 0
        return self.pitches[-1] - self.pitches[0]

    def interval_between(self, voice_a: int, voice_b: int) -> int:
        """Return the interval in semitones between two voices.

        Args:
            voice_a: Index of the first voice (0=lowest).
            voice_b: Index of the second voice.

        Returns:
            Interval in semitones.
        """
        return abs(self.pitches[voice_b] - self.pitches[voice_a])


def check_parallel_fifths(
    voicing_a: Voicing,
    voicing_b: Voicing,
) -> list[tuple[int, int]]:
    """Detect parallel perfect fifths between two successive voicings.

    Parallel fifths occur when two voices are a perfect fifth apart
    in both voicings, and both voices move in the same direction.

    Args:
        voicing_a: The first voicing (before).
        voicing_b: The second voicing (after).

    Returns:
        List of (voice_i, voice_j) pairs that form parallel fifths.
    """
    return _check_parallel_interval(voicing_a, voicing_b, 7)


def check_parallel_octaves(
    voicing_a: Voicing,
    voicing_b: Voicing,
) -> list[tuple[int, int]]:
    """Detect parallel octaves between two successive voicings.

    Args:
        voicing_a: The first voicing.
        voicing_b: The second voicing.

    Returns:
        List of (voice_i, voice_j) pairs that form parallel octaves.
    """
    return _check_parallel_interval(voicing_a, voicing_b, 12)


def _check_parallel_interval(
    voicing_a: Voicing,
    voicing_b: Voicing,
    interval: int,
) -> list[tuple[int, int]]:
    """Detect parallel motion at a specific interval.

    Args:
        voicing_a: The first voicing.
        voicing_b: The second voicing.
        interval: The interval in semitones to check (7=fifth, 12=octave).

    Returns:
        List of voice index pairs with parallel motion at the given interval.
    """
    n_voices = min(voicing_a.voice_count, voicing_b.voice_count)
    parallels: list[tuple[int, int]] = []

    for i in range(n_voices):
        for j in range(i + 1, n_voices):
            interval_a = (voicing_a.pitches[j] - voicing_a.pitches[i]) % 12
            interval_b = (voicing_b.pitches[j] - voicing_b.pitches[i]) % 12

            if interval_a == interval % 12 and interval_b == interval % 12:
                # Both voicings have this interval — check for similar motion
                motion_i = voicing_b.pitches[i] - voicing_a.pitches[i]
                motion_j = voicing_b.pitches[j] - voicing_a.pitches[j]

                # Parallel = both voices move in the same direction (and move)
                if motion_i != 0 and motion_j != 0 and (motion_i > 0) == (motion_j > 0):
                    parallels.append((i, j))

    return parallels


def voice_distance(voicing_a: Voicing, voicing_b: Voicing) -> int:
    """Calculate total voice movement between two voicings.

    Measures the sum of absolute semitone distances across all voices.
    Lower values indicate smoother voice leading.

    Args:
        voicing_a: The first voicing.
        voicing_b: The second voicing.

    Returns:
        Total semitone distance across all voices.
    """
    n_voices = min(voicing_a.voice_count, voicing_b.voice_count)
    return sum(abs(voicing_b.pitches[i] - voicing_a.pitches[i]) for i in range(n_voices))
