"""EQ processing via pedalboard.

Applies parametric EQ bands (high-pass, low-pass, peak, shelving)
to an audio buffer. All pedalboard imports are confined to this module.

Belongs to Layer 5 (Mix Chain).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

from yao.errors import RenderError
from yao.schema.production import EQBand

_NDFloat = npt.NDArray[np.floating[Any]]

try:
    from pedalboard import (  # type: ignore[attr-defined,unused-ignore]
        HighpassFilter,
        LowpassFilter,
        PeakFilter,
        Pedalboard,
    )

    _HAS_PEDALBOARD = True
except ImportError:
    _HAS_PEDALBOARD = False


def apply_eq(audio: _NDFloat, sr: int, bands: list[EQBand]) -> _NDFloat:
    """Apply a chain of EQ bands to an audio buffer.

    Args:
        audio: Audio array, shape (samples,) or (samples, channels).
        sr: Sample rate.
        bands: Ordered list of EQ bands to apply.

    Returns:
        Processed audio (same shape).

    Raises:
        RenderError: If pedalboard is not installed.
    """
    if not _HAS_PEDALBOARD:
        raise RenderError("pedalboard is not installed. Install with: pip install pedalboard")

    if not bands:
        return audio

    effects: list[Any] = []
    for band in bands:
        if band.type == "high_pass":
            effects.append(HighpassFilter(cutoff_frequency_hz=band.freq))
        elif band.type == "low_pass":
            effects.append(LowpassFilter(cutoff_frequency_hz=band.freq))
        elif band.type == "peak":
            effects.append(
                PeakFilter(
                    cutoff_frequency_hz=band.freq,
                    gain_db=band.gain,
                    q=band.q,
                )
            )
        elif band.type in ("low_shelf", "high_shelf"):
            # pedalboard has LowShelfFilter/HighShelfFilter in some versions;
            # fall back to PeakFilter with wider Q as approximation
            effects.append(
                PeakFilter(
                    cutoff_frequency_hz=band.freq,
                    gain_db=band.gain,
                    q=max(band.q * 0.5, 0.1),
                )
            )

    board = Pedalboard(effects)
    processed: _NDFloat = board(audio.astype(np.float32), sr).astype(audio.dtype)
    return processed
