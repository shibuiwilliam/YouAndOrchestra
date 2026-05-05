"""RhythmSystem — Protocol for diverse rhythmic organizations.

Abstracts the concept of a rhythmic system so that Western meters,
Indian tala, Arabic iqa, and West African bell patterns can all be
expressed through a uniform interface.

The default system is WesternMeter. Non-Western systems provide
cycle lengths and accent patterns that do not map to Western bar lines.

Belongs to Layer 3 (IR).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RhythmSystem(Protocol):
    """Protocol for rhythm system implementations.

    Any rhythm system must provide:
    - A name for identification.
    - Cycle length in beats.
    - Accent pattern per beat position within the cycle.

    Implementations: WesternMeter, TalaSystem, IqaSystem.
    """

    @property
    def name(self) -> str:
        """Human-readable name of this rhythm system."""
        ...

    def cycle_length(self) -> int:
        """Total number of beats in one complete rhythmic cycle.

        Returns:
            Number of beats per cycle.
        """
        ...

    def accent_pattern(self) -> tuple[float, ...]:
        """Accent strength per beat position within the cycle.

        Returns:
            Tuple of accent values in [0.0, 1.0] for each beat.
            Length must equal cycle_length().
        """
        ...


class WesternMeter:
    """Western metric system — 4/4, 3/4, 6/8, etc.

    Implements standard Western metric accent patterns.

    Attributes:
        numerator: Beats per bar.
        denominator: Beat unit (4 = quarter note, 8 = eighth note).
    """

    def __init__(self, numerator: int = 4, denominator: int = 4) -> None:
        """Initialize a Western meter.

        Args:
            numerator: Beats per bar.
            denominator: Beat unit.
        """
        self._numerator = numerator
        self._denominator = denominator

    @property
    def name(self) -> str:
        """Return system name."""
        return f"western_{self._numerator}/{self._denominator}"

    def cycle_length(self) -> int:
        """One bar = one cycle.

        Returns:
            Number of beats per bar.
        """
        return self._numerator

    def accent_pattern(self) -> tuple[float, ...]:
        """Standard Western metric accents.

        Beat 1 = strongest (1.0), other strong beats at 0.7,
        weak beats at 0.3.

        Returns:
            Accent pattern for one bar.
        """
        if self._numerator == 4:
            return (1.0, 0.3, 0.7, 0.3)
        if self._numerator == 3:
            return (1.0, 0.3, 0.3)
        if self._numerator == 6:
            # Compound duple: 6/8 has two groups of 3
            return (1.0, 0.3, 0.3, 0.7, 0.3, 0.3)
        if self._numerator == 5:
            # 5/4: typically 3+2 or 2+3
            return (1.0, 0.3, 0.3, 0.7, 0.3)
        if self._numerator == 7:
            # 7/8: typically 2+2+3 or 3+2+2
            return (1.0, 0.3, 0.7, 0.3, 0.7, 0.3, 0.3)
        # Generic: strong downbeat, equal weak beats
        return (1.0,) + (0.3,) * (self._numerator - 1)


class TalaSystem:
    """Indian tala rhythmic system.

    Talas organize rhythm into cycles (avartana) with structured
    subdivisions (vibhag) and characteristic clap/wave patterns.

    Attributes:
        tala: The tala name (e.g., "tintal", "jhaptal", "rupak").
    """

    _TALA_PATTERNS: dict[str, tuple[tuple[int, ...], tuple[float, ...]]] = {
        # (vibhag_grouping, accent_pattern)
        "tintal": (
            (4, 4, 4, 4),  # 16 beats in 4 vibhags
            (
                1.0,
                0.3,
                0.3,
                0.3,  # Sam (1st clap) — strongest
                0.7,
                0.3,
                0.3,
                0.3,  # 2nd clap
                0.5,
                0.3,
                0.3,
                0.3,  # Khali (wave) — weaker
                0.7,
                0.3,
                0.3,
                0.3,
            ),  # 3rd clap
        ),
        "jhaptal": (
            (2, 3, 2, 3),  # 10 beats
            (
                1.0,
                0.3,  # Sam
                0.7,
                0.3,
                0.3,  # 2nd clap
                0.5,
                0.3,  # Khali
                0.7,
                0.3,
                0.3,
            ),  # 3rd clap
        ),
        "rupak": (
            (3, 2, 2),  # 7 beats
            (
                1.0,
                0.3,
                0.3,  # Sam (starts with khali in rupak)
                0.7,
                0.3,  # Clap
                0.7,
                0.3,
            ),  # Clap
        ),
        "ektal": (
            (2, 2, 2, 2, 2, 2),  # 12 beats
            (
                1.0,
                0.3,  # Sam
                0.5,
                0.3,  # Khali
                0.7,
                0.3,  # Clap
                0.7,
                0.3,  # Clap
                0.5,
                0.3,  # Khali
                0.7,
                0.3,
            ),  # Clap
        ),
    }

    def __init__(self, tala: str = "tintal") -> None:
        """Initialize with a tala name.

        Args:
            tala: Tala name.

        Raises:
            ValueError: If tala is not recognized.
        """
        if tala not in self._TALA_PATTERNS:
            msg = f"Unknown tala '{tala}'. Valid: {sorted(self._TALA_PATTERNS.keys())}"
            raise ValueError(msg)
        self._tala = tala

    @property
    def name(self) -> str:
        """Return system name."""
        return f"tala_{self._tala}"

    def cycle_length(self) -> int:
        """Return the total number of beats in one avartana (cycle).

        Returns:
            Total beats.
        """
        grouping, _ = self._TALA_PATTERNS[self._tala]
        return sum(grouping)

    def accent_pattern(self) -> tuple[float, ...]:
        """Return the accent pattern for one cycle.

        Reflects the clap/wave (tali/khali) structure.

        Returns:
            Accent values per beat.
        """
        _, pattern = self._TALA_PATTERNS[self._tala]
        return pattern


class IqaSystem:
    """Arabic iqa rhythmic system.

    Iqa'at are rhythmic patterns defined by sequences of dum (bass)
    and tak (treble) strokes with specific accent patterns.

    Attributes:
        iqa: The iqa name (e.g., "maqsoum", "masmoudi", "baladi").
    """

    _IQA_PATTERNS: dict[str, tuple[int, tuple[float, ...]]] = {
        # (cycle_beats, accent_pattern)
        "maqsoum": (
            8,
            (1.0, 0.3, 0.7, 0.3, 0.5, 0.3, 0.7, 0.3),  # D . T . t . T .
        ),
        "masmoudi_kabir": (
            8,
            (1.0, 0.3, 1.0, 0.3, 0.5, 0.3, 0.7, 0.3),  # D . D . t . T .
        ),
        "baladi": (
            4,
            (1.0, 0.3, 0.7, 0.3),  # D . T .
        ),
        "saidi": (
            4,
            (1.0, 0.7, 0.3, 0.7),  # D D . T
        ),
        "wahda": (
            4,
            (1.0, 0.3, 0.3, 0.3),  # D . . .
        ),
    }

    def __init__(self, iqa: str = "maqsoum") -> None:
        """Initialize with an iqa name.

        Args:
            iqa: Iqa name.

        Raises:
            ValueError: If iqa is not recognized.
        """
        if iqa not in self._IQA_PATTERNS:
            msg = f"Unknown iqa '{iqa}'. Valid: {sorted(self._IQA_PATTERNS.keys())}"
            raise ValueError(msg)
        self._iqa = iqa

    @property
    def name(self) -> str:
        """Return system name."""
        return f"iqa_{self._iqa}"

    def cycle_length(self) -> int:
        """Return the total number of beats in one cycle.

        Returns:
            Total beats.
        """
        beats, _ = self._IQA_PATTERNS[self._iqa]
        return beats

    def accent_pattern(self) -> tuple[float, ...]:
        """Return the accent pattern for one cycle.

        Reflects the dum/tak structure.

        Returns:
            Accent values per beat.
        """
        _, pattern = self._IQA_PATTERNS[self._iqa]
        return pattern
