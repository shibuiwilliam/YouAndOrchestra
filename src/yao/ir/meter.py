"""MeterSpec — structured meter representation for YaO's IR.

MeterSpec is a frozen dataclass that replaces raw time signature strings
with structured information about beat grouping, compound detection,
pulse unit, and metric accents.

This is internal domain IR (Layer 1). For external YAML parsing, use
``yao.schema.time_signature.TimeSignatureSpec``.
"""

from __future__ import annotations

from dataclasses import dataclass

from yao.errors import SpecValidationError
from yao.ir.timing import beats_per_bar_from_sig, is_compound, parse_time_signature


@dataclass(frozen=True)
class MeterSpec:
    """Structured meter specification.

    Attributes:
        numerator: Top number (e.g. 7 in 7/8).
        denominator: Bottom number (e.g. 8 in 7/8).
        grouping: Beat grouping in denominator units (e.g. (3, 2, 2) for 7/8).
        is_compound: True for 6/8, 9/8, 12/8 compound meters.
        pulse_unit: Duration of one pulse in quarter-note beats.
        metric_accents: Accent weight per grouping position (1.0 = strongest).
    """

    numerator: int
    denominator: int
    grouping: tuple[int, ...]
    is_compound: bool
    pulse_unit: float
    metric_accents: tuple[float, ...]

    def beats_per_bar(self) -> float:
        """Return the number of quarter-note beats in one bar."""
        return beats_per_bar_from_sig(self.numerator, self.denominator)

    def group_count(self) -> int:
        """Return the number of beat groups in one bar."""
        return len(self.grouping)

    def group_durations_beats(self) -> tuple[float, ...]:
        """Return duration of each group in quarter-note beats."""
        unit = 4.0 / self.denominator
        return tuple(g * unit for g in self.grouping)

    @classmethod
    def from_time_signature(
        cls,
        ts: str,
        groupings: list[int] | None = None,
    ) -> MeterSpec:
        """Create a MeterSpec from a time signature string.

        Args:
            ts: Time signature string (e.g. "7/8", "4/4", "6/8").
            groupings: Explicit beat groupings in denominator units.
                If None, auto-groups: compound → 3s, simple 4/4 → (1,1,1,1).

        Returns:
            A new MeterSpec.

        Raises:
            SpecValidationError: If the time signature is malformed or
                groupings don't sum to numerator.
        """
        num, den = parse_time_signature(ts)
        compound = is_compound(ts)

        if groupings is not None:
            if sum(groupings) != num:
                raise SpecValidationError(
                    f"Groupings {groupings} sum to {sum(groupings)}, but numerator is {num}",
                    field="meter.grouping",
                )
            grp = tuple(groupings)
        elif compound:
            grp = tuple([3] * (num // 3))
        else:
            grp = tuple([1] * num)

        # Compute pulse unit: for compound meters, one pulse = dotted quarter
        pulse = 3.0 * (4.0 / den) if compound else 4.0 / den

        # Generate metric accents: first group is strongest,
        # subsequent groups get decreasing weight
        accents = _compute_accents(grp)

        return cls(
            numerator=num,
            denominator=den,
            grouping=grp,
            is_compound=compound,
            pulse_unit=pulse,
            metric_accents=accents,
        )


def parse_meter_string(ts: str, groupings: list[int] | None = None) -> MeterSpec:
    """Parse a time signature string into a MeterSpec.

    Convenience function wrapping ``MeterSpec.from_time_signature()``.

    Args:
        ts: Time signature string (e.g. "7/8", "4/4").
        groupings: Optional explicit beat groupings.

    Returns:
        A MeterSpec instance.
    """
    return MeterSpec.from_time_signature(ts, groupings)


def _compute_accents(grouping: tuple[int, ...]) -> tuple[float, ...]:
    """Compute metric accent weights per grouping position.

    The first group always gets weight 1.0 (downbeat).
    Subsequent groups get decreasing weights based on position.

    Args:
        grouping: Beat grouping in denominator units.

    Returns:
        Tuple of accent weights, one per group.
    """
    n = len(grouping)
    if n == 0:
        return ()
    if n == 1:
        return (1.0,)

    accents: list[float] = [1.0]  # downbeat
    for i in range(1, n):
        # Midpoint of the bar gets secondary accent
        if n >= 4 and i == n // 2:  # noqa: PLR2004
            accents.append(0.75)
        else:
            # Other positions get lighter weight, slightly varied
            accents.append(round(0.5 + 0.1 * (i % 2), 2))
    return tuple(accents)
