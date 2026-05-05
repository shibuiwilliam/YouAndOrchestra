"""Sound Design effects — effect chain definitions.

An EffectChain is an ordered list of audio effects applied to a stem
during rendering. Effects are defined declaratively; the actual DSP
processing happens in the render layer (Layer 5) using pedalboard or
similar backends.

Belongs to Layer 3.5 (Sound Design).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from yao.errors import SpecValidationError

# Supported effect types
EffectType = Literal[
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

VALID_EFFECT_TYPES: frozenset[str] = frozenset(
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


@dataclass(frozen=True)
class Effect:
    """A single audio effect with its parameters.

    Attributes:
        effect_type: The type of effect (eq, compressor, reverb, etc.).
        parameters: Effect-specific parameters.
            For eq: {"frequency_hz": 1000, "gain_db": -3, "q": 1.0}
            For compressor: {"threshold_db": -20, "ratio": 4.0, ...}
            For reverb: {"room_size": 0.7, "damping": 0.5, "wet": 0.3}
            For delay: {"time_ms": 250, "feedback": 0.4, "wet": 0.25}
            For tape_saturation: {"drive": 0.6, "warmth": 0.4}
            For bitcrusher: {"bit_depth": 12, "sample_rate": 22050}
        bypass: Whether the effect is bypassed (inactive but preserved).
    """

    effect_type: EffectType
    parameters: dict[str, object] = field(default_factory=dict)
    bypass: bool = False

    def __post_init__(self) -> None:
        """Validate effect fields."""
        if self.effect_type not in VALID_EFFECT_TYPES:
            raise SpecValidationError(
                f"Invalid effect type: {self.effect_type!r}. Must be one of: {sorted(VALID_EFFECT_TYPES)}",
                field="effect_type",
            )


@dataclass(frozen=True)
class EffectChain:
    """An ordered chain of effects applied to a single stem.

    Effects are applied in order (first in list = first in signal chain).

    Attributes:
        name: Identifier for this chain (e.g., "piano_chain", "drums_bus").
        effects: Ordered list of effects in the signal chain.
    """

    name: str
    effects: tuple[Effect, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate effect chain fields."""
        if not self.name:
            raise SpecValidationError("EffectChain name must not be empty", field="name")

    @property
    def active_effects(self) -> tuple[Effect, ...]:
        """Return only non-bypassed effects."""
        return tuple(e for e in self.effects if not e.bypass)

    @property
    def is_empty(self) -> bool:
        """Return True if no active effects exist."""
        return len(self.active_effects) == 0
