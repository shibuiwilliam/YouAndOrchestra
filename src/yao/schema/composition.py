"""Pydantic models for composition.yaml specification.

These models validate external YAML input. They belong to Layer 1 (Specification)
and have no dependencies on upper layers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, field_validator

from yao.constants.music import DYNAMICS_TO_VELOCITY, SCALE_INTERVALS
from yao.errors import SpecValidationError


class InstrumentSpec(BaseModel):
    """Specification for a single instrument in the composition."""

    name: str
    role: Literal["melody", "harmony", "bass", "rhythm", "pad", "counter_melody"]
    counter_to: str | None = None
    density_factor: float = 0.5

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise SpecValidationError("Instrument name cannot be empty", field="name")
        return v.strip()


class SectionSpec(BaseModel):
    """Specification for a single section (intro, verse, chorus, etc.)."""

    name: str
    bars: int
    tempo_bpm: float | None = None
    time_signature: str | None = None
    key: str | None = None
    dynamics: str = "mf"

    @field_validator("bars")
    @classmethod
    def bars_positive(cls, v: int) -> int:
        if v <= 0:
            raise SpecValidationError(f"Section bars must be positive, got {v}", field="bars")
        return v

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        if not v.strip():
            raise SpecValidationError("Section name cannot be empty", field="name")
        return v.strip()

    @field_validator("dynamics")
    @classmethod
    def dynamics_valid(cls, v: str) -> str:
        if v not in DYNAMICS_TO_VELOCITY:
            raise SpecValidationError(
                f"Unknown dynamics '{v}'. Valid: {list(DYNAMICS_TO_VELOCITY.keys())}",
                field="dynamics",
            )
        return v


class GenerationConfig(BaseModel):
    """Configuration for the generation strategy.

    Attributes:
        strategy: Generator name (e.g., "rule_based", "stochastic").
        seed: Random seed for reproducibility (stochastic generators).
        temperature: Variation control (0.0=conservative, 1.0=adventurous).
    """

    strategy: str = "rule_based"
    seed: int | None = None
    temperature: float = 0.5

    @field_validator("temperature")
    @classmethod
    def temperature_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Temperature must be 0.0–1.0, got {v}",
                field="generation.temperature",
            )
        return v


class DrumsSpec(BaseModel):
    """Drum pattern specification (optional).

    When present, the drum_patterner generator produces drum hits
    alongside the pitched instruments. Backward compatible — existing
    specs without this field continue to work without drums.
    """

    pattern_family: str
    swing: float = 0.0
    humanize_ms: float = 0.0
    ghost_notes_density: float = 0.0
    fills_at: list[str] = []  # noqa: RUF012

    @field_validator("swing")
    @classmethod
    def swing_in_range(cls, v: float) -> float:
        """Swing must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(f"swing must be 0.0–1.0, got {v}", field="drums.swing")
        return v

    @field_validator("ghost_notes_density")
    @classmethod
    def ghost_density_in_range(cls, v: float) -> float:
        """Ghost notes density must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"ghost_notes_density must be 0.0–1.0, got {v}",
                field="drums.ghost_notes_density",
            )
        return v


class CompositionSpec(BaseModel):
    """Top-level specification for a composition.

    Validated from composition.yaml. All fields have sensible defaults
    so that a minimal spec (title + instruments + sections) is sufficient.
    """

    title: str
    genre: str = "general"
    key: str = "C major"
    tempo_bpm: float = 120.0
    time_signature: str = "4/4"
    total_bars: int = 0
    instruments: list[InstrumentSpec]
    sections: list[SectionSpec]
    drums: DrumsSpec | None = None
    generation: GenerationConfig = GenerationConfig()

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise SpecValidationError("Title cannot be empty", field="title")
        return v.strip()

    @field_validator("key")
    @classmethod
    def key_valid(cls, v: str) -> str:
        parts = v.split()
        if len(parts) != 2:  # noqa: PLR2004
            raise SpecValidationError(
                f"Key must be 'Note Scale' (e.g., 'C major'), got '{v}'",
                field="key",
            )
        scale_type = parts[1]
        if scale_type not in SCALE_INTERVALS:
            raise SpecValidationError(
                f"Unknown scale type '{scale_type}'. Valid: {list(SCALE_INTERVALS.keys())}",
                field="key",
            )
        return v

    @field_validator("tempo_bpm")
    @classmethod
    def tempo_reasonable(cls, v: float) -> float:
        if not 20.0 <= v <= 300.0:
            raise SpecValidationError(
                f"Tempo must be between 20 and 300 BPM, got {v}",
                field="tempo_bpm",
            )
        return v

    @field_validator("time_signature")
    @classmethod
    def time_signature_valid(cls, v: str) -> str:
        parts = v.split("/")
        if len(parts) != 2:  # noqa: PLR2004
            raise SpecValidationError(
                f"Time signature must be 'N/D' (e.g., '4/4'), got '{v}'",
                field="time_signature",
            )
        try:
            num, den = int(parts[0]), int(parts[1])
        except (IndexError, TypeError) as e:
            raise SpecValidationError(f"Invalid time signature '{v}'", field="time_signature") from e
        if num <= 0 or den <= 0:
            raise SpecValidationError(
                f"Time signature components must be positive, got '{v}'",
                field="time_signature",
            )
        return v

    @field_validator("sections")
    @classmethod
    def sections_not_empty(cls, v: list[SectionSpec]) -> list[SectionSpec]:
        if not v:
            raise SpecValidationError("At least one section is required", field="sections")
        return v

    @field_validator("instruments")
    @classmethod
    def instruments_not_empty(cls, v: list[InstrumentSpec]) -> list[InstrumentSpec]:
        if not v:
            raise SpecValidationError("At least one instrument is required", field="instruments")
        return v

    def computed_total_bars(self) -> int:
        """Return total_bars if set, otherwise sum of section bars."""
        if self.total_bars > 0:
            return self.total_bars
        return sum(s.bars for s in self.sections)

    @classmethod
    def from_yaml(cls, path: Path) -> CompositionSpec:
        """Load and validate a composition spec from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Validated CompositionSpec.

        Raises:
            SpecValidationError: If the YAML is invalid or fails validation.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load YAML: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Spec validation failed: {e}") from e
