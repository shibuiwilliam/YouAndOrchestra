"""Centralized timing conversions.

ALL tick/beat/second conversions MUST go through this module.
Never compute ticks manually elsewhere (CLAUDE.md §7, failure pattern F1).

Extended in v2.0 with compound meter and beat grouping support.
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
    num, den = parse_time_signature(time_signature)
    bpb = beats_per_bar_from_sig(num, den)
    return bars * bpb


def beats_to_bars(beats: Beat, time_signature: str = "4/4") -> float:
    """Convert beats to bars (may be fractional).

    Args:
        beats: Number of beats.
        time_signature: Time signature string.

    Returns:
        Number of bars (float).
    """
    num, den = parse_time_signature(time_signature)
    bpb = beats_per_bar_from_sig(num, den)
    if bpb <= 0:
        return 0.0
    return beats / bpb


# ---------------------------------------------------------------------------
# Extended time signature utilities (v2.0)
# ---------------------------------------------------------------------------


def parse_time_signature(ts: str) -> tuple[int, int]:
    """Parse a time signature string into (numerator, denominator).

    Args:
        ts: Time signature string (e.g., "7/8", "4/4").

    Returns:
        Tuple of (numerator, denominator).

    Raises:
        SpecValidationError: If the string is malformed.
    """
    parts = ts.split("/")
    if len(parts) != 2:  # noqa: PLR2004
        raise SpecValidationError(
            f"Invalid time signature '{ts}'",
            field="time_signature",
        )
    try:
        num = int(parts[0])
        den = int(parts[1])
    except (ValueError, TypeError) as e:
        raise SpecValidationError(
            f"Invalid time signature '{ts}'",
            field="time_signature",
        ) from e
    if num <= 0 or den <= 0:
        raise SpecValidationError(
            f"Time signature components must be positive, got '{ts}'",
            field="time_signature",
        )
    return num, den


def beats_per_bar_from_sig(numerator: int, denominator: int) -> float:
    """Calculate beats per bar from numerator and denominator.

    Beats are in quarter-note units.
    4/4 → 4.0, 3/4 → 3.0, 6/8 → 3.0, 7/8 → 3.5.

    Args:
        numerator: Top number of the time signature.
        denominator: Bottom number.

    Returns:
        Beats per bar in quarter-note units.
    """
    return numerator * (4.0 / denominator)


def is_compound(ts: str) -> bool:
    """Return True if the time signature is compound meter.

    Compound: numerator divisible by 3, greater than 3, denominator is 8.
    Examples: 6/8, 9/8, 12/8.

    Args:
        ts: Time signature string.

    Returns:
        True if compound.
    """
    num, den = parse_time_signature(ts)
    return num % 3 == 0 and num > 3 and den == 8  # noqa: PLR2004


def beat_grouping(
    ts: str,
    groupings: list[int] | None = None,
) -> list[float]:
    """Return beat durations for each group within a bar.

    For 7/8 with groupings [3, 2, 2]:
    Each "8th note" = 0.5 quarter-note beats.
    Groups: [3*0.5, 2*0.5, 2*0.5] = [1.5, 1.0, 1.0]

    For compound 6/8 (auto-grouped [3, 3]):
    Groups: [3*0.5, 3*0.5] = [1.5, 1.5]

    Args:
        ts: Time signature string.
        groupings: Explicit beat groupings (in denominator units).
            If None, auto-groups: compound→3s, simple→1s.

    Returns:
        List of beat durations in quarter-note beats.
    """
    num, den = parse_time_signature(ts)
    unit_beats = 4.0 / den  # duration of one denominator unit in quarter-beats

    if groupings is not None:
        return [g * unit_beats for g in groupings]

    # Auto-grouping
    if is_compound(ts):
        return [3 * unit_beats] * (num // 3)

    return [unit_beats] * num
