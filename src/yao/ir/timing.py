"""Centralized timing conversions.

ALL tick/beat/second conversions MUST go through this module.
Never compute ticks manually elsewhere (CLAUDE.md §7, failure pattern F1).
"""

from __future__ import annotations

from yao.constants.midi import DEFAULT_PPQ
from yao.errors import SpecValidationError
from yao.types import BPM, Beat, Seconds, Tick


def beats_to_ticks(beats: Beat, ppq: int = DEFAULT_PPQ) -> Tick:
    """Convert beats to MIDI ticks.

    Args:
        beats: Number of beats (quarter notes).
        ppq: Pulses per quarter note.

    Returns:
        Number of MIDI ticks.
    """
    return round(beats * ppq)


def ticks_to_beats(ticks: Tick, ppq: int = DEFAULT_PPQ) -> Beat:
    """Convert MIDI ticks to beats.

    Args:
        ticks: Number of MIDI ticks.
        ppq: Pulses per quarter note.

    Returns:
        Number of beats.
    """
    return ticks / ppq


def beats_to_seconds(beats: Beat, bpm: BPM) -> Seconds:
    """Convert beats to wall-clock seconds.

    Args:
        beats: Number of beats.
        bpm: Tempo in beats per minute.

    Returns:
        Duration in seconds.
    """
    return beats * 60.0 / bpm


def seconds_to_beats(seconds: Seconds, bpm: BPM) -> Beat:
    """Convert wall-clock seconds to beats.

    Args:
        seconds: Duration in seconds.
        bpm: Tempo in beats per minute.

    Returns:
        Number of beats.
    """
    return seconds * bpm / 60.0


def bars_to_beats(bars: int, time_signature: str = "4/4") -> Beat:
    """Convert a number of bars to beats.

    Args:
        bars: Number of bars.
        time_signature: Time signature string (e.g., "4/4", "3/4", "6/8").

    Returns:
        Number of beats.

    Raises:
        SpecValidationError: If time_signature is malformed.
    """
    parts = time_signature.split("/")
    if len(parts) != 2:  # noqa: PLR2004
        raise SpecValidationError(
            f"Invalid time signature '{time_signature}'",
            field="time_signature",
        )
    try:
        numerator = int(parts[0])
        denominator = int(parts[1])
    except (IndexError, TypeError) as e:
        raise SpecValidationError(
            f"Invalid time signature '{time_signature}'",
            field="time_signature",
        ) from e

    # Beats per bar: numerator * (4 / denominator)
    # e.g., 4/4 -> 4 beats, 3/4 -> 3 beats, 6/8 -> 3 beats
    beats_per_bar = numerator * (4.0 / denominator)
    return bars * beats_per_bar
