"""Pydantic models for production.yaml specification.

Defines mix and mastering parameters: LUFS target, stereo width,
reverb, and other final audio processing settings.
Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError


class ProductionSpec(BaseModel):
    """Mix and mastering specification.

    Attributes:
        target_lufs: Target integrated loudness in LUFS.
        stereo_width: Stereo width percentage (0.0=mono, 1.0=full stereo).
        reverb_amount: Global reverb send level (0.0–1.0).
        master_eq: Optional master EQ description.
    """

    target_lufs: float = -14.0
    stereo_width: float = 0.8
    reverb_amount: float = 0.3
    master_eq: str = ""

    @field_validator("target_lufs")
    @classmethod
    def lufs_reasonable(cls, v: float) -> float:
        if not -30.0 <= v <= 0.0:
            raise SpecValidationError(
                f"LUFS target must be between -30 and 0, got {v}",
                field="target_lufs",
            )
        return v

    @field_validator("stereo_width")
    @classmethod
    def width_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Stereo width must be 0.0–1.0, got {v}",
                field="stereo_width",
            )
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> ProductionSpec:
        """Load from a YAML file.

        Args:
            path: Path to production.yaml.

        Returns:
            Validated ProductionSpec.

        Raises:
            SpecValidationError: If loading fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load production spec: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Production YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Production validation failed: {e}") from e
