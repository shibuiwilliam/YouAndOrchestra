"""Pydantic models for negative-space.yaml specification.

Negative space defines what NOT to play: intentional silence, frequency gaps,
and texture reductions. Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from yao.errors import SpecValidationError


class SilenceRegion(BaseModel):
    """A region of intentional silence.

    Attributes:
        start_bar: Starting bar of the silence.
        end_bar: Ending bar (exclusive).
        instruments: Which instruments are silent (empty = all).
    """

    start_bar: int
    end_bar: int
    instruments: list[str] = []


class FrequencyGap(BaseModel):
    """A frequency range to keep clear.

    Attributes:
        low_hz: Lower bound in Hz.
        high_hz: Upper bound in Hz.
        sections: Which sections this gap applies to (empty = all).
    """

    low_hz: float
    high_hz: float
    sections: list[str] = []


class NegativeSpaceSpec(BaseModel):
    """Specification of what NOT to play.

    Attributes:
        silences: Regions of intentional silence.
        frequency_gaps: Frequency ranges to keep clear.
        max_simultaneous_instruments: Maximum instruments playing at once.
        rest_ratio: Target ratio of rest to sound (0.0–1.0).
    """

    silences: list[SilenceRegion] = []
    frequency_gaps: list[FrequencyGap] = []
    max_simultaneous_instruments: int | None = None
    rest_ratio: float | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> NegativeSpaceSpec:
        """Load from a YAML file.

        Args:
            path: Path to negative-space.yaml.

        Returns:
            Validated NegativeSpaceSpec.

        Raises:
            SpecValidationError: If loading fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load negative space: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Negative space YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Negative space validation failed: {e}") from e
