"""Pydantic model for hooks.yaml specification.

Defines hooks (memorable fragments) and their deployment strategies.
Cross-spec validation ensures motif_ref matches existing MotifPlan seeds
and appearance positions exist within declared sections.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from yao.errors import SpecValidationError


class HookAppearanceSpec(BaseModel):
    """A single appearance position for a hook.

    Attributes:
        section_id: Section where the hook appears.
        bar: Bar number within the section (0-indexed).
    """

    section_id: str
    bar: int = 0

    @field_validator("bar")
    @classmethod
    def bar_non_negative(cls, v: int) -> int:
        """Bar must be non-negative."""
        if v < 0:
            raise SpecValidationError(f"Bar must be >= 0, got {v}", field="hooks.appearances.bar")
        return v


class HookSpec(BaseModel):
    """Specification for a single hook.

    Attributes:
        id: Unique hook identifier.
        motif_ref: Reference to a MotifSeed.id.
        deployment: Deployment strategy.
        appearances: Ordered list of positions.
        variations_allowed: Whether variations are acceptable.
        maximum_uses: Maximum number of appearances.
        distinctive_strength: How memorable this hook is [0, 1].
    """

    id: str
    motif_ref: str
    deployment: Literal["rare", "frequent", "withhold_then_release", "ascending_repetition"] = "frequent"
    appearances: list[HookAppearanceSpec] = Field(default_factory=list)
    variations_allowed: bool = True
    maximum_uses: int = 4
    distinctive_strength: float = 0.8

    @field_validator("distinctive_strength")
    @classmethod
    def strength_in_range(cls, v: float) -> float:
        """distinctive_strength must be in [0, 1]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"distinctive_strength must be 0.0–1.0, got {v}",
                field="hooks.distinctive_strength",
            )
        return v

    @field_validator("maximum_uses")
    @classmethod
    def max_uses_positive(cls, v: int) -> int:
        """maximum_uses must be positive."""
        if v < 1:
            raise SpecValidationError(
                f"maximum_uses must be >= 1, got {v}",
                field="hooks.maximum_uses",
            )
        return v


class HooksSpec(BaseModel):
    """Root model for hooks.yaml.

    Attributes:
        hooks: List of hook definitions.
    """

    hooks: list[HookSpec] = Field(default_factory=list)

    @field_validator("hooks")
    @classmethod
    def unique_ids(cls, v: list[HookSpec]) -> list[HookSpec]:
        """Hook IDs must be unique."""
        ids = [h.id for h in v]
        if len(ids) != len(set(ids)):
            dupes = [hid for hid in ids if ids.count(hid) > 1]
            raise SpecValidationError(
                f"Duplicate hook IDs: {set(dupes)}",
                field="hooks",
            )
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> HooksSpec:
        """Load HooksSpec from a YAML file.

        Args:
            path: Path to hooks.yaml.

        Returns:
            Validated HooksSpec.

        Raises:
            SpecValidationError: If the file is invalid.
        """
        if not path.exists():
            raise SpecValidationError(f"hooks.yaml not found: {path}", field="hooks")
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SpecValidationError(f"Invalid YAML in hooks.yaml: {e}", field="hooks") from e
        if data is None:
            return cls(hooks=[])
        if not isinstance(data, dict):
            raise SpecValidationError("hooks.yaml root must be a mapping", field="hooks")
        return cls.model_validate(data)
