"""Pydantic models for extended time signature specification.

Supports simple strings ("4/4"), compound meters ("6/8"), odd meters
with beat groupings ("7/8" [3,2,2]), and polymeter declarations.

The ``time_signature`` field in composition.yaml accepts both string
and object forms for backward compatibility.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

from yao.errors import SpecValidationError


class PolymeterTrack(BaseModel):
    """A single track in a polymetric layout.

    Attributes:
        instrument: Instrument name this applies to.
        time_signature: Time signature for this track.
        sync_at: Bar number where all tracks re-synchronize.
    """

    instrument: str
    time_signature: str
    sync_at: int

    @field_validator("sync_at")
    @classmethod
    def sync_at_positive(cls, v: int) -> int:
        """sync_at must be positive."""
        if v <= 0:
            raise SpecValidationError(
                f"Polymeter sync_at must be positive, got {v}",
                field="sync_at",
            )
        return v


class TimeSignatureSpec(BaseModel):
    """Extended time signature specification.

    Supports:
    - Simple: ``primary="4/4"``
    - Compound: ``primary="6/8", compound=True``
    - Odd with groupings: ``primary="7/8", beat_groupings=[3, 2, 2]``
    - Polymeter: ``polymeter=[PolymeterTrack(...)]``

    Attributes:
        primary: Time signature string (e.g., "7/8").
        beat_groupings: How beats are grouped within a bar.
            Must sum to the numerator of primary.
        compound: Whether this is compound meter (auto-detected if None).
        polymeter: Optional polymetric track declarations.
    """

    primary: str = "4/4"
    beat_groupings: list[int] | None = None
    compound: bool | None = None
    polymeter: list[PolymeterTrack] | None = None

    @field_validator("primary")
    @classmethod
    def primary_valid(cls, v: str) -> str:
        """Validate primary time signature format."""
        parts = v.split("/")
        if len(parts) != 2:  # noqa: PLR2004
            raise SpecValidationError(
                f"Time signature must be 'N/D', got '{v}'",
                field="time_signature",
            )
        try:
            num, den = int(parts[0]), int(parts[1])
        except (ValueError, TypeError) as e:
            raise SpecValidationError(
                f"Invalid time signature '{v}'",
                field="time_signature",
            ) from e
        if num <= 0 or den <= 0:
            raise SpecValidationError(
                f"Time signature components must be positive, got '{v}'",
                field="time_signature",
            )
        return v

    @model_validator(mode="after")
    def validate_groupings(self) -> TimeSignatureSpec:
        """Validate that beat_groupings sum to the numerator."""
        if self.beat_groupings is not None:
            num = int(self.primary.split("/")[0])
            total = sum(self.beat_groupings)
            if total != num:
                raise SpecValidationError(
                    f"beat_groupings {self.beat_groupings} sum to {total}, "
                    f"but primary '{self.primary}' has numerator {num}",
                    field="beat_groupings",
                )
        return self

    @model_validator(mode="after")
    def validate_polymeter_sync(self) -> TimeSignatureSpec:
        """Validate that polymeter tracks have sync_at."""
        if self.polymeter is not None:
            for track in self.polymeter:
                if track.sync_at <= 0:
                    raise SpecValidationError(
                        f"Polymeter track '{track.instrument}' missing valid sync_at",
                        field="polymeter",
                    )
        return self

    def numerator(self) -> int:
        """Return the numerator of the primary time signature."""
        return int(self.primary.split("/")[0])

    def denominator(self) -> int:
        """Return the denominator of the primary time signature."""
        return int(self.primary.split("/")[1])

    def is_compound(self) -> bool:
        """Return True if this is compound meter.

        Compound meter: numerator divisible by 3 and denominator is 8.
        Examples: 6/8, 9/8, 12/8.
        """
        if self.compound is not None:
            return self.compound
        num = self.numerator()
        den = self.denominator()
        return num % 3 == 0 and num > 3 and den == 8  # noqa: PLR2004

    def get_beat_grouping(self) -> list[int]:
        """Return beat groupings for this time signature.

        If explicit groupings are provided, use them.
        For compound meters, group in 3s.
        Otherwise, group in 1s (simple meter).

        Returns:
            List of beat group sizes in denominator units.
        """
        if self.beat_groupings is not None:
            return list(self.beat_groupings)
        num = self.numerator()
        if self.is_compound():
            return [3] * (num // 3)
        return [1] * num
