"""Pydantic models for groove.yaml specification.

Defines the groove configuration for a project. Supports selecting
a base groove profile with optional overrides.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from yao.errors import SpecValidationError


class GrooveOverrides(BaseModel):
    """Optional overrides applied on top of a base groove profile.

    Attributes:
        swing_ratio: Override swing ratio [0, 1].
        timing_jitter_sigma: Override jitter sigma in ms.
        ghost_probability: Override ghost note probability [0, 1].
    """

    swing_ratio: float | None = None
    timing_jitter_sigma: float | None = None
    ghost_probability: float | None = None

    @field_validator("swing_ratio")
    @classmethod
    def swing_in_range(cls, v: float | None) -> float | None:
        """Swing ratio must be in [0, 1]."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"swing_ratio must be in [0, 1], got {v}",
                field="groove.overrides.swing_ratio",
            )
        return v

    @field_validator("timing_jitter_sigma")
    @classmethod
    def jitter_non_negative(cls, v: float | None) -> float | None:
        """Jitter sigma must be non-negative."""
        if v is not None and v < 0:
            raise SpecValidationError(
                f"timing_jitter_sigma must be >= 0, got {v}",
                field="groove.overrides.timing_jitter_sigma",
            )
        return v

    @field_validator("ghost_probability")
    @classmethod
    def ghost_in_range(cls, v: float | None) -> float | None:
        """Ghost probability must be in [0, 1]."""
        if v is not None and not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"ghost_probability must be in [0, 1], got {v}",
                field="groove.overrides.ghost_probability",
            )
        return v


class GrooveSpec(BaseModel):
    """Top-level groove.yaml specification.

    Attributes:
        schema_version: Schema version string.
        base: Name of a groove profile from grooves/ (e.g., "lofi_hiphop").
        overrides: Optional parameter overrides on top of the base profile.
        apply_to_all_instruments: Whether groove applies to all instruments.
    """

    schema_version: str = "1.0"
    base: str = ""
    overrides: GrooveOverrides = Field(default_factory=GrooveOverrides)
    apply_to_all_instruments: bool = True

    @field_validator("base")
    @classmethod
    def base_not_whitespace(cls, v: str) -> str:
        """Base must be stripped."""
        return v.strip()

    @classmethod
    def from_yaml(cls, path: Path) -> GrooveSpec:
        """Load from a YAML file.

        Args:
            path: Path to groove.yaml.

        Returns:
            Validated GrooveSpec.

        Raises:
            SpecValidationError: If loading or validation fails.
        """
        try:
            with open(path) as f:
                data: Any = yaml.safe_load(f) or {}
            # Handle nested "groove:" key
            if "groove" in data and isinstance(data["groove"], dict):
                data = {**data["groove"], **{k: v for k, v in data.items() if k != "groove"}}
            return cls.model_validate(data)
        except Exception as e:
            if isinstance(e, SpecValidationError):
                raise
            raise SpecValidationError(
                f"Failed to load groove.yaml: {e}",
                field="groove",
            ) from e
