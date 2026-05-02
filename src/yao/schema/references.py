"""Pydantic models for references.yaml specification.

Defines the aesthetic reference library — positive (emulate) and negative
(avoid) reference works with strict copyright protection.

**Copyright safety** (defense in depth):
1. Schema level: ``extract_features`` validated against allowlist.
2. Schema level: ``forbidden_to_extract`` items rejected if in ``extract_features``.
3. Schema level: ``rights_status="unknown"`` → ``MissingRightsStatusError``.
4. Runtime: ``ReferenceMatcher`` re-checks before extraction.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator

from yao.errors import MissingRightsStatusError, SpecValidationError

# Features that may be safely extracted (abstract, non-copyrightable)
ALLOWED_FEATURES: frozenset[str] = frozenset(
    {
        "harmonic_rhythm",
        "voice_leading_smoothness",
        "rhythmic_density_per_bar",
        "register_distribution",
        "timbre_centroid_curve",
        "motif_density",
    }
)

# Features that must NEVER be extracted (copyrightable elements)
FORBIDDEN_FEATURES: frozenset[str] = frozenset(
    {
        "melody_contour",
        "melody",
        "chord_sequence",
        "chord_progression",
        "chords",
        "lyrics",
        "hook",
    }
)


class PrimaryReference(BaseModel):
    """A positive reference — a work to draw stylistic inspiration from.

    Attributes:
        file: Path to the reference file (relative to references/).
        role: Description of what this reference provides.
        weight: Influence weight (0.0-1.0).
        extract_features: Which features to extract (must be in ALLOWED_FEATURES).
        forbidden_to_extract: Explicit blocklist (defense in depth).
        rights_status: License status (must not be "unknown").
    """

    file: str
    role: str
    weight: float = 0.5
    extract_features: list[str] = []  # noqa: RUF012
    forbidden_to_extract: list[str] = []  # noqa: RUF012
    rights_status: str

    @field_validator("rights_status")
    @classmethod
    def rights_not_unknown(cls, v: str) -> str:
        """Reject unknown rights status."""
        if v.lower() in ("unknown", ""):
            raise MissingRightsStatusError(
                f"Reference rights_status must not be '{v}'. All references require explicit licensing."
            )
        return v

    @field_validator("extract_features")
    @classmethod
    def features_in_allowlist(cls, v: list[str]) -> list[str]:
        """Ensure all requested features are in the allowlist."""
        for feat in v:
            if feat in FORBIDDEN_FEATURES:
                raise SpecValidationError(
                    f"Feature '{feat}' is in FORBIDDEN_FEATURES and cannot be extracted.",
                    field="extract_features",
                )
            if feat not in ALLOWED_FEATURES:
                raise SpecValidationError(
                    f"Feature '{feat}' not in ALLOWED_FEATURES. Valid: {sorted(ALLOWED_FEATURES)}",
                    field="extract_features",
                )
        return v


class NegativeReference(BaseModel):
    """A negative reference — a work whose style should be avoided.

    Attributes:
        file: Path to the reference file.
        role: Description of what to avoid.
        avoid_features: Which abstract features to measure distance from.
        rights_status: License status.
    """

    file: str
    role: str
    avoid_features: list[str] = []  # noqa: RUF012
    rights_status: str

    @field_validator("rights_status")
    @classmethod
    def rights_not_unknown(cls, v: str) -> str:
        """Reject unknown rights status."""
        if v.lower() in ("unknown", ""):
            raise MissingRightsStatusError(f"Reference rights_status must not be '{v}'.")
        return v


class ReferencesSpec(BaseModel):
    """Specification of aesthetic references for a composition.

    Attributes:
        primary: References to emulate.
        negative: References to avoid.
    """

    primary: list[PrimaryReference] = []  # noqa: RUF012
    negative: list[NegativeReference] = []  # noqa: RUF012

    @classmethod
    def from_yaml(cls, path: Path) -> ReferencesSpec:
        """Load from a YAML file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load references: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("References YAML root must be a mapping")
        if "references" in data:
            data = data["references"]
        try:
            return cls.model_validate(data)
        except (SpecValidationError, MissingRightsStatusError):
            raise
        except Exception as e:
            raise SpecValidationError(f"References validation failed: {e}") from e
