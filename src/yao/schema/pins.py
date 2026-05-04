"""Pydantic models for pins.yaml specification.

Pins are auto-managed by the CLI. Users create pins via the
``yao pin`` command; they do not edit pins.yaml directly.
Pins are immutable — once written, they must not be modified.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from yao.errors import SpecValidationError


class PinLocationSpec(BaseModel):
    """Location of a pin within the composition.

    Attributes:
        section: Section name.
        bar: Bar number (1-indexed).
        beat: Beat within the bar (1-indexed). Optional.
        instrument: Instrument name. Optional.
    """

    section: str
    bar: int = Field(ge=1)
    beat: float | None = None
    instrument: str | None = None


class PinSpec(BaseModel):
    """A single pin entry.

    Attributes:
        id: Unique pin identifier.
        location: Where in the piece this pin targets.
        note: User's natural-language comment.
        user_intent: Parsed intent.
        severity: Importance level.
        created_at: ISO 8601 timestamp.
    """

    id: str
    location: PinLocationSpec
    note: str
    user_intent: str = "unclear"
    severity: Literal["low", "medium", "high"] = "medium"
    created_at: str = ""

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        """Pin id must be non-empty."""
        if not v.strip():
            raise SpecValidationError("Pin id cannot be empty", field="pins.id")
        return v.strip()

    @field_validator("note")
    @classmethod
    def note_not_empty(cls, v: str) -> str:
        """Pin note must be non-empty."""
        if not v.strip():
            raise SpecValidationError("Pin note cannot be empty", field="pins.note")
        return v.strip()


class PinsSpec(BaseModel):
    """Top-level pins.yaml specification.

    Attributes:
        schema_version: Schema version string.
        project: Project name.
        iteration: Iteration this pin set applies to.
        pins: List of pin entries.
    """

    schema_version: str = "1.0"
    project: str = ""
    iteration: str = ""
    pins: list[PinSpec] = Field(default_factory=list)

    def pin_ids(self) -> list[str]:
        """Return all pin ids."""
        return [p.id for p in self.pins]

    def pins_for_section(self, section: str) -> list[PinSpec]:
        """Return pins targeting a specific section."""
        return [p for p in self.pins if p.location.section == section]

    @classmethod
    def from_yaml(cls, path: Path) -> PinsSpec:
        """Load from a YAML file.

        Args:
            path: Path to pins.yaml.

        Returns:
            Validated PinsSpec.

        Raises:
            SpecValidationError: If loading or validation fails.
        """
        try:
            with open(path) as f:
                data: Any = yaml.safe_load(f) or {}
            return cls.model_validate(data)
        except Exception as e:
            if isinstance(e, SpecValidationError):
                raise
            raise SpecValidationError(
                f"Failed to load pins.yaml: {e}",
                field="pins",
            ) from e

    def to_yaml(self, path: Path) -> None:
        """Write to a YAML file.

        Args:
            path: Path to write pins.yaml.
        """
        data = self.model_dump()
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
