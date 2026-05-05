"""Sound Design patches — synthesis kind and parameter definitions.

A Patch represents a timbre configuration for a single instrument voice.
It specifies the synthesis method and its parameters without coupling
to any particular rendering engine.

Belongs to Layer 3.5 (Sound Design).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from yao.errors import SpecValidationError

# Supported synthesis kinds
SynthesisKind = Literal[
    "sample_based",
    "subtractive",
    "fm",
    "wavetable",
    "physical",
]

# Valid synthesis kinds as a set for runtime checking
VALID_SYNTHESIS_KINDS: frozenset[str] = frozenset(["sample_based", "subtractive", "fm", "wavetable", "physical"])


@dataclass(frozen=True)
class Patch:
    """A timbre patch defining synthesis method and parameters.

    Attributes:
        name: Human-readable patch name (e.g., "warm_pad", "pluck_bass").
        synthesis_kind: The synthesis method to use.
        parameters: Key-value parameters specific to the synthesis kind.
            For sample_based: {"soundfont": "path.sf2", "preset": 0}
            For subtractive: {"oscillator": "saw", "cutoff_hz": 800, ...}
            For fm: {"carrier_ratio": 1.0, "modulator_ratio": 2.0, ...}
            For wavetable: {"table": "basic_shapes", "position": 0.5}
            For physical: {"model": "karplus_strong", "damping": 0.5}
    """

    name: str
    synthesis_kind: SynthesisKind
    parameters: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate patch fields."""
        if not self.name:
            raise SpecValidationError("Patch name must not be empty", field="name")
        if self.synthesis_kind not in VALID_SYNTHESIS_KINDS:
            raise SpecValidationError(
                f"Invalid synthesis kind: {self.synthesis_kind!r}. Must be one of: {sorted(VALID_SYNTHESIS_KINDS)}",
                field="synthesis_kind",
            )
