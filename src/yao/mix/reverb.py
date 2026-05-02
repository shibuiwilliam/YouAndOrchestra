"""Reverb processing via pedalboard.

Provides 4 presets (hall, room, plate, spring) mapped to
pedalboard.Reverb parameters. Belongs to Layer 5 (Mix Chain).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from yao.errors import RenderError
from yao.schema.production import ReverbSpec

_NDFloat = npt.NDArray[np.floating[Any]]

try:
    from pedalboard import Pedalboard, Reverb  # type: ignore[attr-defined,unused-ignore]

    _HAS_PEDALBOARD = True
except ImportError:
    _HAS_PEDALBOARD = False

# Preset → (room_size, damping, width) base values.
# wet_level and decay are taken from the ReverbSpec.
_REVERB_PRESETS: dict[str, tuple[float, float, float]] = {
    "hall": (0.8, 0.5, 1.0),
    "room": (0.4, 0.7, 0.8),
    "plate": (0.6, 0.3, 1.0),
    "spring": (0.3, 0.8, 0.6),
}


def apply_reverb(
    audio: _NDFloat,
    sr: int,
    spec: ReverbSpec,
) -> _NDFloat:
    """Apply reverb to an audio buffer.

    Args:
        audio: Audio array, shape (samples,) or (samples, channels).
        sr: Sample rate.
        spec: Reverb parameters including preset type.

    Returns:
        Audio with reverb applied (same shape).

    Raises:
        RenderError: If pedalboard is not installed.
    """
    if not _HAS_PEDALBOARD:
        raise RenderError("pedalboard is not installed. Install with: pip install pedalboard")

    room_size, damping, width = _REVERB_PRESETS.get(spec.type, _REVERB_PRESETS["hall"])

    reverb = Reverb(
        room_size=room_size,
        damping=damping,
        wet_level=spec.wet,
        dry_level=1.0 - spec.wet,
        width=width,
    )
    board = Pedalboard([reverb])
    processed: _NDFloat = board(audio.astype(np.float32), sr).astype(audio.dtype)
    return processed
