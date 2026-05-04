"""Pydantic models for tension_arcs.yaml specification.

Defines short-range (2–8 bar) tension–resolution structures that
decouple local drama from macro trajectory curves.

Cross-spec validation: section names referenced here must exist in
composition.yaml's form.sections.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from yao.errors import SpecValidationError


class ArcLocationSpec(BaseModel):
    """Location of a tension arc within the piece.

    Attributes:
        section: Section identifier (must exist in composition.yaml).
        bars: Two-element list [start_bar, end_bar] (1-indexed, inclusive).
    """

    section: str
    bars: list[int] = Field(min_length=2, max_length=2)

    @field_validator("bars")
    @classmethod
    def bars_ordered(cls, v: list[int]) -> list[int]:
        """Bar range must be ordered and span 2–8 bars."""
        if len(v) != 2:
            raise SpecValidationError(
                f"bars must have exactly 2 elements, got {len(v)}",
                field="tension_arcs.location.bars",
            )
        start, end = v
        span = end - start + 1
        if span < 2 or span > 8:
            raise SpecValidationError(
                f"TensionArc span must be 2–8 bars, got {span} (bars: {v})",
                field="tension_arcs.location.bars",
            )
        if start < 1:
            raise SpecValidationError(
                f"Bar numbers are 1-indexed, got start={start}",
                field="tension_arcs.location.bars",
            )
        return v


class ArcReleaseSpec(BaseModel):
    """Where a tension arc resolves.

    Attributes:
        section: Section identifier for the release point.
        bar: Bar number within the section (1-indexed).
    """

    section: str
    bar: int = Field(ge=1)


class TensionArcSpec(BaseModel):
    """A single tension arc specification.

    Attributes:
        id: Unique identifier for this arc.
        location: Where in the piece this arc lives.
        pattern: Shape of the tension curve.
        target_release: Where the arc resolves. None if unresolved.
        intensity: Peak intensity [0, 1].
        mechanism: Harmonic mechanism description.
    """

    id: str
    location: ArcLocationSpec
    pattern: Literal["linear_rise", "dip", "plateau", "spike", "deceptive"]
    target_release: ArcReleaseSpec | None = None
    intensity: float = Field(ge=0.0, le=1.0, default=0.5)
    mechanism: str = ""

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        """Arc id must be non-empty."""
        if not v.strip():
            raise SpecValidationError(
                "TensionArc id cannot be empty",
                field="tension_arcs.id",
            )
        return v.strip()


class TensionArcsSpec(BaseModel):
    """Top-level tension_arcs.yaml specification.

    Attributes:
        schema_version: Schema version string.
        tension_arcs: List of tension arc definitions.
    """

    schema_version: str = "1.0"
    tension_arcs: list[TensionArcSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids(self) -> TensionArcsSpec:
        """All arc ids must be unique."""
        ids = [arc.id for arc in self.tension_arcs]
        dupes = [x for x in ids if ids.count(x) > 1]
        if dupes:
            raise SpecValidationError(
                f"Duplicate tension arc ids: {set(dupes)}",
                field="tension_arcs",
            )
        return self

    def validate_against_sections(self, section_ids: list[str]) -> list[str]:
        """Validate that all referenced sections exist.

        Args:
            section_ids: Valid section identifiers from composition.yaml.

        Returns:
            List of error messages. Empty if all valid.
        """
        errors: list[str] = []
        for arc in self.tension_arcs:
            if arc.location.section not in section_ids:
                errors.append(f"TensionArc '{arc.id}' references unknown section '{arc.location.section}'")
            if arc.target_release and arc.target_release.section not in section_ids:
                errors.append(
                    f"TensionArc '{arc.id}' release references unknown section '{arc.target_release.section}'"
                )
        return errors

    @classmethod
    def from_yaml(cls, path: Path) -> TensionArcsSpec:
        """Load from a YAML file.

        Args:
            path: Path to tension_arcs.yaml.

        Returns:
            Validated TensionArcsSpec.

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
                f"Failed to load tension_arcs.yaml: {e}",
                field="tension_arcs",
            ) from e
