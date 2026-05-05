"""Sound Design specification schema — Pydantic validation for YAML specs.

Validates the sound_design section of a composition spec, defining
patches and effect chains for each voice/stem.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError

# Mirror the valid values from sound_design layer for schema validation
VALID_SYNTHESIS_KINDS = frozenset(["sample_based", "subtractive", "fm", "wavetable", "physical"])

VALID_EFFECT_TYPES = frozenset(
    [
        "eq",
        "compressor",
        "limiter",
        "reverb",
        "convolution_reverb",
        "delay",
        "tape_saturation",
        "bitcrusher",
        "chorus",
        "phaser",
        "flanger",
    ]
)


class PatchSpec(BaseModel):
    """Schema for a synthesis patch specification."""

    name: str
    synthesis_kind: Literal["sample_based", "subtractive", "fm", "wavetable", "physical"]
    parameters: dict[str, Any] = {}

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Ensure patch name is non-empty."""
        if not v.strip():
            raise SpecValidationError("Patch name must not be empty", field="name")
        return v


class EffectSpec(BaseModel):
    """Schema for a single effect in an effect chain."""

    effect_type: Literal[
        "eq",
        "compressor",
        "limiter",
        "reverb",
        "convolution_reverb",
        "delay",
        "tape_saturation",
        "bitcrusher",
        "chorus",
        "phaser",
        "flanger",
    ]
    parameters: dict[str, Any] = {}
    bypass: bool = False


class EffectChainSpec(BaseModel):
    """Schema for an ordered chain of effects."""

    name: str
    effects: list[EffectSpec] = []

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Ensure chain name is non-empty."""
        if not v.strip():
            raise SpecValidationError("EffectChain name must not be empty", field="name")
        return v


class SoundDesignSpec(BaseModel):
    """Top-level sound design specification for a composition.

    Maps voice/stem names to their patch and effect chain configurations.

    Example YAML:
        sound_design:
          patches:
            piano:
              name: warm_piano
              synthesis_kind: sample_based
              parameters:
                soundfont: "piano.sf2"
                preset: 0
          effect_chains:
            piano:
              name: piano_chain
              effects:
                - effect_type: eq
                  parameters: {frequency_hz: 200, gain_db: -2, q: 0.7}
                - effect_type: reverb
                  parameters: {room_size: 0.6, wet: 0.25}
    """

    patches: dict[str, PatchSpec] = {}
    effect_chains: dict[str, EffectChainSpec] = {}

    @field_validator("patches")
    @classmethod
    def validate_patches(cls, v: dict[str, PatchSpec]) -> dict[str, PatchSpec]:
        """Validate that all patch entries have valid configurations."""
        for stem_name, _patch in v.items():
            if not stem_name.strip():
                raise SpecValidationError(
                    "Stem name for patch must not be empty",
                    field="patches",
                )
        return v

    @field_validator("effect_chains")
    @classmethod
    def validate_chains(cls, v: dict[str, EffectChainSpec]) -> dict[str, EffectChainSpec]:
        """Validate that all effect chain entries have valid configurations."""
        for stem_name, _chain in v.items():
            if not stem_name.strip():
                raise SpecValidationError(
                    "Stem name for effect chain must not be empty",
                    field="effect_chains",
                )
        return v
