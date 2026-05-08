"""Feature flags for v3.0 Combination Stack modules.

Each flag gates a Layer 2.5 module. When a flag is ``False``, the
corresponding module returns its input unchanged (identity behavior).

Defaults are conservative: only the highest-impact wins from Phase 3.5
are enabled by default (chord_aware_melody, voice_leading_optimization).

Belongs to Layer 1 (Specification).

See CLAUDE.md Non-Negotiable Rule 9, PROJECT.md §7.2.
"""

from __future__ import annotations

from pydantic import BaseModel


class FeatureFlags(BaseModel):
    """Feature flags controlling v3.0 Combination Stack modules.

    Users can set these in their composition.yaml under the ``features:``
    key. Unset flags use the defaults listed below.

    Attributes:
        chord_aware_melody: Gate for §4.1. When True, M2 scores candidates
            against HarmonicMelodyConstraints. Default: True.
        voice_leading_optimization: Gate for §5.4. When True, the Orchestrator
            uses the voice-leading optimizer for chord voicings. Default: True.
        reharmonization: Gate for §5.1. When True, reharmonization operations
            may be applied. Default: False (opt-in).
    """

    chord_aware_melody: bool = True
    voice_leading_optimization: bool = True
    reharmonization: bool = False
