"""Pydantic models for references.yaml specification.

Defines the aesthetic reference library — positive (emulate) and negative
(avoid) reference works. Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from yao.errors import SpecValidationError


class ReferenceEntry(BaseModel):
    """A single reference work in the aesthetic library.

    Attributes:
        id: Unique identifier for this reference.
        description: Abstract feature description (no artist names).
        polarity: Whether to emulate (positive) or avoid (negative).
        extract: Which features to extract from this reference.
    """

    id: str
    description: str
    polarity: Literal["positive", "negative"] = "positive"
    extract: list[str] = []


class ReferencesSpec(BaseModel):
    """Specification of aesthetic references for a composition.

    Attributes:
        positive: References to emulate.
        negative: References to avoid.
    """

    positive: list[ReferenceEntry] = []
    negative: list[ReferenceEntry] = []

    @classmethod
    def from_yaml(cls, path: Path) -> ReferencesSpec:
        """Load from a YAML file.

        Args:
            path: Path to references.yaml.

        Returns:
            Validated ReferencesSpec.

        Raises:
            SpecValidationError: If loading fails.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load references: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("References YAML root must be a mapping")
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"References validation failed: {e}") from e
