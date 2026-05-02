"""Pydantic models for arrangement.yaml specification.

Defines the arrangement contract: what to preserve, what to transform,
and the rights status of the source material.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator

from yao.errors import MissingRightsStatusError, SpecValidationError


class PreservationSpec(BaseModel):
    """What to preserve from the source.

    Attributes:
        melody: Preserve melody contour.
        hook_rhythm: Preserve rhythmic hook.
        chord_function: Preserve harmonic function.
        form: Preserve song form structure.
    """

    melody: bool = True
    melody_similarity_min: float = 0.85
    hook_rhythm: bool = True
    hook_similarity_min: float = 0.80
    chord_function: bool = True
    chord_similarity_min: float = 0.75
    form: bool = True


class TransformSpec(BaseModel):
    """What to transform in the arrangement.

    Attributes:
        target_genre: Target genre for style transfer.
        bpm: Target BPM (None = keep original).
        reharmonization_level: How much to reharmonize (0.0-1.0).
        swing: Swing amount for the target.
        groove: Groove description.
    """

    target_genre: str = "general"
    bpm: float | None = None
    reharmonization_level: float = 0.0
    swing: float = 0.0
    groove: str = ""

    @field_validator("reharmonization_level")
    @classmethod
    def reharm_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"reharmonization_level must be 0.0-1.0, got {v}",
                field="reharmonization_level",
            )
        return v


class ArrangementInputSpec(BaseModel):
    """Source material specification.

    Attributes:
        file: Path to source MIDI file.
        rights_status: License status (must not be unknown).
    """

    file: str
    rights_status: str

    @field_validator("rights_status")
    @classmethod
    def rights_not_unknown(cls, v: str) -> str:
        if v.lower() in ("unknown", ""):
            raise MissingRightsStatusError(
                f"Arrangement input rights_status must not be '{v}'. Source material requires explicit licensing."
            )
        return v


class ArrangementSpec(BaseModel):
    """Complete arrangement specification.

    Attributes:
        input: Source material specification.
        preserve: What to keep from the source.
        transform: What to change.
    """

    input: ArrangementInputSpec
    preserve: PreservationSpec = PreservationSpec()
    transform: TransformSpec = TransformSpec()

    @classmethod
    def from_yaml(cls, path: Path) -> ArrangementSpec:
        """Load from a YAML file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load arrangement spec: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Arrangement YAML root must be a mapping")
        if "arrangement" in data:
            data = data["arrangement"]
        try:
            return cls.model_validate(data)
        except (SpecValidationError, MissingRightsStatusError):
            raise
        except Exception as e:
            raise SpecValidationError(f"Arrangement validation failed: {e}") from e
