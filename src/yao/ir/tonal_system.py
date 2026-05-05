"""TonalSystem — Protocol for diverse tonal organizations.

Abstracts the concept of a tonal system so that Western common practice,
modal, maqam, raga, and microtonal systems can all be expressed through
a uniform interface.

The default system is CommonPracticeTonality (12-TET, functional harmony).
Non-Western systems override scale realization and cadence semantics.

Belongs to Layer 3 (IR).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TonalSystem(Protocol):
    """Protocol for tonal system implementations.

    Any tonal system must provide:
    - A name for identification.
    - Scale realization: given a root, produce the scale in cents.
    - Cadence strength: rate how strongly one chord resolves to another.

    Implementations: CommonPracticeTonality, ModalSystem, MaqamSystem.
    """

    @property
    def name(self) -> str:
        """Human-readable name of this tonal system."""
        ...

    def realize_scale(self, root_midi: int) -> tuple[float, ...]:
        """Realize a scale from a root pitch, returning cents from A4.

        Args:
            root_midi: MIDI note number for the root.

        Returns:
            Tuple of cents values for each scale degree.
        """
        ...

    def cadence_strength(self, prev_degree: int, curr_degree: int) -> float:
        """Rate cadence strength between two scale degrees.

        Args:
            prev_degree: Previous chord's scale degree (0-indexed).
            curr_degree: Current chord's scale degree (0-indexed).

        Returns:
            Float in [0.0, 1.0]. 1.0 = strongest resolution.
        """
        ...


class CommonPracticeTonality:
    """Western common-practice tonality (12-TET, functional harmony).

    The default tonal system. Realizes scales in 12-tone equal temperament
    and rates cadences by standard functional harmony rules.
    """

    @property
    def name(self) -> str:
        """Return system name."""
        return "common_practice"

    def realize_scale(self, root_midi: int) -> tuple[float, ...]:
        """Realize a major scale in 12-TET cents.

        Args:
            root_midi: MIDI note number for the root.

        Returns:
            7-degree major scale in cents from A4.
        """
        from yao.ir.tuning import Tuning

        intervals = (0, 2, 4, 5, 7, 9, 11)  # major scale semitones
        return tuple(Tuning.cents_from_a4(root_midi + i) for i in intervals)

    def cadence_strength(self, prev_degree: int, curr_degree: int) -> float:
        """Rate cadence strength in common-practice harmony.

        V→I = 1.0 (authentic), IV→I = 0.8 (plagal), etc.

        Args:
            prev_degree: Previous degree (0=I, 1=II, ..., 6=VII).
            curr_degree: Current degree.

        Returns:
            Cadence strength in [0.0, 1.0].
        """
        # V→I (authentic cadence) — strongest
        if prev_degree == 4 and curr_degree == 0:
            return 1.0
        # IV→I (plagal cadence)
        if prev_degree == 3 and curr_degree == 0:
            return 0.8
        # vii°→I
        if prev_degree == 6 and curr_degree == 0:
            return 0.9
        # V→vi (deceptive)
        if prev_degree == 4 and curr_degree == 5:
            return 0.6
        # Any→V (half cadence)
        if curr_degree == 4:
            return 0.5
        # ii→V
        if prev_degree == 1 and curr_degree == 4:
            return 0.7
        return 0.3


class ModalSystem:
    """Modal system — church modes (dorian, phrygian, lydian, etc.).

    Uses 12-TET tuning but with mode-specific scale patterns
    and cadence semantics that differ from common practice.

    Attributes:
        mode: The mode name (e.g., "dorian", "phrygian", "lydian").
    """

    _MODE_INTERVALS: dict[str, tuple[int, ...]] = {
        "ionian": (0, 2, 4, 5, 7, 9, 11),
        "dorian": (0, 2, 3, 5, 7, 9, 10),
        "phrygian": (0, 1, 3, 5, 7, 8, 10),
        "lydian": (0, 2, 4, 6, 7, 9, 11),
        "mixolydian": (0, 2, 4, 5, 7, 9, 10),
        "aeolian": (0, 2, 3, 5, 7, 8, 10),
        "locrian": (0, 1, 3, 5, 6, 8, 10),
    }

    def __init__(self, mode: str = "dorian") -> None:
        """Initialize with a mode name.

        Args:
            mode: Mode name. Must be one of the 7 church modes.

        Raises:
            ValueError: If mode is not recognized.
        """
        if mode not in self._MODE_INTERVALS:
            msg = f"Unknown mode '{mode}'. Valid: {sorted(self._MODE_INTERVALS.keys())}"
            raise ValueError(msg)
        self._mode = mode

    @property
    def name(self) -> str:
        """Return system name."""
        return f"modal_{self._mode}"

    def realize_scale(self, root_midi: int) -> tuple[float, ...]:
        """Realize the mode's scale in 12-TET cents.

        Args:
            root_midi: MIDI note number for the root.

        Returns:
            7-degree modal scale in cents from A4.
        """
        from yao.ir.tuning import Tuning

        intervals = self._MODE_INTERVALS[self._mode]
        return tuple(Tuning.cents_from_a4(root_midi + i) for i in intervals)

    def cadence_strength(self, prev_degree: int, curr_degree: int) -> float:
        """Rate cadence strength in modal context.

        Modal cadences differ from common practice: the characteristic
        degree of each mode acts as a secondary tonal center.

        Args:
            prev_degree: Previous degree (0-indexed).
            curr_degree: Current degree (0-indexed).

        Returns:
            Cadence strength in [0.0, 1.0].
        """
        # In modal music, resolution to the tonic is still strongest
        if curr_degree == 0:
            return 0.8
        # Movement to the characteristic degree is also strong
        # Dorian: degree 5 (vi), Phrygian: degree 1 (bII), Lydian: degree 3 (#IV)
        characteristic = {"dorian": 5, "phrygian": 1, "lydian": 3, "mixolydian": 6, "aeolian": 5}
        if self._mode in characteristic and curr_degree == characteristic[self._mode]:
            return 0.6
        return 0.3


class MaqamSystem:
    """Arabic/Turkish maqam system with quarter-tone support.

    Maqamat use intervals not available in 12-TET, including
    three-quarter tones (150 cents) and neutral intervals.

    Attributes:
        maqam: The maqam name (e.g., "rast", "bayati", "hijaz").
    """

    # Intervals in cents from root for common maqamat
    _MAQAM_CENTS: dict[str, tuple[float, ...]] = {
        "rast": (0, 200, 350, 500, 700, 900, 1050),  # C D E↓ F G A B↓
        "bayati": (0, 150, 300, 500, 700, 850, 1000),  # D E↓ F G A B↓ C
        "hijaz": (0, 100, 400, 500, 700, 800, 1100),  # D Eb F# G A Bb C#
        "saba": (0, 150, 300, 400, 700, 800, 1000),  # D E↓ F Gb A Bb C
        "nahawand": (0, 200, 300, 500, 700, 800, 1100),  # natural minor with raised 7th
    }

    def __init__(self, maqam: str = "rast") -> None:
        """Initialize with a maqam name.

        Args:
            maqam: Maqam name. Must be one of the known maqamat.

        Raises:
            ValueError: If maqam is not recognized.
        """
        if maqam not in self._MAQAM_CENTS:
            msg = f"Unknown maqam '{maqam}'. Valid: {sorted(self._MAQAM_CENTS.keys())}"
            raise ValueError(msg)
        self._maqam = maqam

    @property
    def name(self) -> str:
        """Return system name."""
        return f"maqam_{self._maqam}"

    def realize_scale(self, root_midi: int) -> tuple[float, ...]:
        """Realize the maqam's scale in cents from A4.

        Uses quarter-tone intervals that deviate from 12-TET.

        Args:
            root_midi: MIDI note number for the root.

        Returns:
            7-degree maqam scale in absolute cents from A4.
        """
        from yao.ir.tuning import Tuning

        root_cents = Tuning.cents_from_a4(root_midi)
        return tuple(root_cents + offset for offset in self._MAQAM_CENTS[self._maqam])

    def cadence_strength(self, prev_degree: int, curr_degree: int) -> float:
        """Rate cadence strength in maqam context.

        Maqam cadences emphasize descent to the tonic (qarar) and
        the ghammaz (dominant-equivalent, usually degree 4).

        Args:
            prev_degree: Previous degree (0-indexed).
            curr_degree: Current degree (0-indexed).

        Returns:
            Cadence strength in [0.0, 1.0].
        """
        # Resolution to qarar (tonic, degree 0)
        if curr_degree == 0:
            return 0.9
        # Movement to ghammaz (degree 4, dominant equivalent)
        if curr_degree == 4:
            return 0.6
        # Stepwise descent is typical
        if prev_degree == curr_degree + 1:
            return 0.5
        return 0.3
