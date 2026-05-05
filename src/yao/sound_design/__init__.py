"""Layer 3.5: Sound Design — patches, effects, and synthesis configuration.

This layer sits between IR (Layer 1) and Render (Layer 5). It defines
sound design specifications that transform abstract ScoreIR into
timbre-aware rendering instructions.

IMPORTANT: The `pedalboard` library is an OPTIONAL dependency.
It is imported lazily — missing pedalboard degrades gracefully to
MIDI-only output without crashing.

Allowed imports: constants, schema, ir only.
"""

from __future__ import annotations

from yao.sound_design.effects import Effect, EffectChain
from yao.sound_design.patches import Patch, SynthesisKind

# Lazy pedalboard availability flag
SOUND_DESIGN_AVAILABLE: bool = False

try:
    import pedalboard as _pedalboard  # noqa: F401

    SOUND_DESIGN_AVAILABLE = True
except ImportError:
    pass


__all__ = [
    "Effect",
    "EffectChain",
    "Patch",
    "SOUND_DESIGN_AVAILABLE",
    "SynthesisKind",
]
