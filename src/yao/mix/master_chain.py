"""Master bus processing — compression, limiting, and LUFS normalization.

The master chain is the final processing stage before export.
LUFS normalization uses ``pyloudnorm.normalize.loudness`` exclusively
(no RMS-based approximation). True-peak limiting uses pedalboard.Limiter.

Belongs to Layer 5 (Mix Chain).
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import numpy.typing as npt
import pyloudnorm
import structlog

from yao.errors import RenderError
from yao.mix.compression import apply_compression
from yao.schema.production import MasterSpec

_NDFloat = npt.NDArray[np.floating[Any]]

logger = structlog.get_logger()

try:
    from pedalboard import Limiter, Pedalboard  # type: ignore[attr-defined,unused-ignore]

    _HAS_PEDALBOARD = True
except ImportError:
    _HAS_PEDALBOARD = False


def apply_master(
    audio: _NDFloat,
    sr: int,
    spec: MasterSpec,
) -> _NDFloat:
    """Apply master bus processing chain.

    Processing order:
    1. Optional compression (if spec.compression is set).
    2. True-peak limiting to spec.true_peak_max_dbfs.
    3. LUFS normalization to spec.target_lufs via pyloudnorm.

    Args:
        audio: Stereo or mono audio array.
        sr: Sample rate.
        spec: Master bus specification.

    Returns:
        Mastered audio.

    Raises:
        RenderError: If pedalboard is not installed.
    """
    if not _HAS_PEDALBOARD:
        raise RenderError("pedalboard is not installed. Install with: pip install pedalboard")

    result = audio.copy()

    # 1. Optional master compression
    if spec.compression is not None:
        result = apply_compression(result, sr, spec.compression)

    # 2. True-peak limiter
    limiter = Limiter(threshold_db=spec.true_peak_max_dbfs)
    board = Pedalboard([limiter])
    result = board(result.astype(np.float32), sr).astype(audio.dtype)

    # 3. LUFS normalization
    result = _normalize_lufs(result, sr, spec.target_lufs)

    # 4. Verify true-peak
    peak_db = float(20.0 * np.log10(max(float(np.max(np.abs(result))), 1e-10)))
    if peak_db > spec.true_peak_max_dbfs + 0.1:
        logger.warning(
            "true_peak_exceeded",
            peak_dbfs=round(peak_db, 2),
            limit_dbfs=spec.true_peak_max_dbfs,
        )

    return result


def _normalize_lufs(
    audio: _NDFloat,
    sr: int,
    target_lufs: float,
) -> _NDFloat:
    """Normalize audio to target LUFS using pyloudnorm.

    Args:
        audio: Audio array.
        sr: Sample rate.
        target_lufs: Target integrated loudness in LUFS.

    Returns:
        Loudness-normalized audio.
    """
    meter = pyloudnorm.Meter(sr)
    audio_f64 = audio.astype(np.float64)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        current_lufs: float = meter.integrated_loudness(audio_f64)

    if np.isinf(current_lufs) or np.isnan(current_lufs):
        logger.warning("lufs_normalization_skipped", reason="silence or invalid signal")
        return audio

    normalized: _NDFloat = pyloudnorm.normalize.loudness(audio_f64, current_lufs, target_lufs)
    return normalized.astype(audio.dtype)
