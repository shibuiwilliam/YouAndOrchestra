"""Tonal System schema — v2.0 multi-genre harmonic framework.

Replaces the flat `key: "C major"` string with a polymorphic tonal system
that dispatches to different harmonic realization and evaluation strategies.

Finding C1: The evaluator's quality metrics must be parameterized by tonal system.
A blues b3 is a feature, not a defect. A drone's low pitch class variety is intentional.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError

# All supported tonal system kinds
TonalSystemKind = Literal[
    "tonal_major_minor",
    "modal",
    "pentatonic",
    "blues",
    "microtonal",
    "atonal",
    "drone",
    "raga",
    "maqam",
    "custom",
]

# Modal scale types
MODAL_MODES = [
    "ionian",
    "dorian",
    "phrygian",
    "lydian",
    "mixolydian",
    "aeolian",
    "locrian",
]


class TonalSystem(BaseModel):
    """Polymorphic tonal system specification.

    The `kind` field determines which harmonic realization and evaluation
    strategies apply. Not all fields are relevant for all kinds.

    Attributes:
        kind: The tonal framework (dispatches all downstream behavior).
        key: Root pitch class (e.g., "C", "D", "F#"). For drone, this is the drone note.
        mode: Scale mode (for kind=modal or kind=tonal_major_minor).
        raga: Raga name (for kind=raga only).
        maqam: Maqam name (for kind=maqam only).
        microtonal_resolution: EDO divisions per octave (for kind=microtonal).
        reference_pitch_hz: A4 tuning reference (default 440.0).
        custom_intervals: Semitone intervals for kind=custom.
    """

    kind: TonalSystemKind = "tonal_major_minor"
    key: str = "C"
    mode: str = "major"
    raga: str | None = None
    maqam: str | None = None
    microtonal_resolution: int = 12
    reference_pitch_hz: float = 440.0
    custom_intervals: list[float] | None = None

    model_config = {"extra": "forbid"}

    @field_validator("key")
    @classmethod
    def key_not_empty(cls, v: str) -> str:
        """Key must be a non-empty pitch class name."""
        if not v.strip():
            raise SpecValidationError("Tonal system key cannot be empty", field="tonal_system.key")
        return v.strip()

    @field_validator("microtonal_resolution")
    @classmethod
    def resolution_positive(cls, v: int) -> int:
        """Microtonal resolution must be positive."""
        if v < 1:
            raise SpecValidationError(
                f"Microtonal resolution must be >= 1, got {v}",
                field="tonal_system.microtonal_resolution",
            )
        return v

    @field_validator("reference_pitch_hz")
    @classmethod
    def reference_pitch_reasonable(cls, v: float) -> float:
        """Reference pitch must be in audible range."""
        if not (400.0 <= v <= 480.0):
            raise SpecValidationError(
                f"Reference pitch must be 400-480 Hz, got {v}",
                field="tonal_system.reference_pitch_hz",
            )
        return v

    @property
    def is_consonance_applicable(self) -> bool:
        """Whether consonance-based evaluation applies to this system."""
        return self.kind not in {"atonal", "drone", "microtonal"}

    @property
    def is_pitch_class_variety_applicable(self) -> bool:
        """Whether pitch class variety is a meaningful metric."""
        return self.kind not in {"drone"}

    @property
    def allows_blue_notes(self) -> bool:
        """Whether blue notes (b3, b5, b7) are expected features."""
        return self.kind == "blues"


def promote_legacy_key(key_string: str) -> TonalSystem:
    """Auto-promote a legacy `key: "D minor"` string to a TonalSystem.

    This provides backward compatibility for v1.0 specs.

    Args:
        key_string: Legacy key string like "C major", "D minor", "G dorian".

    Returns:
        Equivalent TonalSystem instance.
    """
    parts = key_string.strip().split()
    if len(parts) < 2:  # noqa: PLR2004
        return TonalSystem(kind="tonal_major_minor", key=parts[0] if parts else "C", mode="major")

    root = parts[0]
    scale_type = parts[1].lower()

    # Map scale types to tonal system kinds
    if scale_type in ("major", "minor"):
        return TonalSystem(kind="tonal_major_minor", key=root, mode=scale_type)
    elif scale_type in MODAL_MODES:
        return TonalSystem(kind="modal", key=root, mode=scale_type)
    elif scale_type in ("pentatonic", "pentatonic_major", "pentatonic_minor"):
        return TonalSystem(kind="pentatonic", key=root, mode=scale_type)
    elif scale_type in ("blues", "blues_minor", "blues_major"):
        return TonalSystem(kind="blues", key=root, mode=scale_type)
    elif scale_type in ("chromatic", "whole_tone"):
        return TonalSystem(kind="tonal_major_minor", key=root, mode=scale_type)
    else:
        # Unknown scale type — default to tonal_major_minor
        return TonalSystem(kind="tonal_major_minor", key=root, mode=scale_type)
