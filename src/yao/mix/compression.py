"""Compression processing via pedalboard.

Wraps pedalboard.Compressor with YaO's CompressionSpec parameters.

Belongs to Layer 5 (Mix Chain).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from yao.errors import RenderError
from yao.schema.production import CompressionSpec

_NDFloat = npt.NDArray[np.floating[Any]]

try:
    from pedalboard import Compressor, Pedalboard  # type: ignore[attr-defined,unused-ignore]

    _HAS_PEDALBOARD = True
except ImportError:
    _HAS_PEDALBOARD = False


def apply_compression(
    audio: _NDFloat,
    sr: int,
    spec: CompressionSpec,
) -> _NDFloat:
    """Apply dynamic range compression to an audio buffer.

    Args:
        audio: Audio array, shape (samples,) or (samples, channels).
        sr: Sample rate.
        spec: Compression parameters.

    Returns:
        Compressed audio (same shape).

    Raises:
        RenderError: If pedalboard is not installed.
    """
    if not _HAS_PEDALBOARD:
        raise RenderError("pedalboard is not installed. Install with: pip install pedalboard")

    compressor = Compressor(
        threshold_db=spec.threshold_db,
        ratio=spec.ratio,
        attack_ms=spec.attack_ms,
        release_ms=spec.release_ms,
    )
    board = Pedalboard([compressor])
    processed: _NDFloat = board(audio.astype(np.float32), sr).astype(audio.dtype)
    return processed
