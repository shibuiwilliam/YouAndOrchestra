"""Simple spec-driven mix chain MVP.

Applies production spec parameters (target_lufs, reverb_amount,
stereo_width) to rendered audio using numpy-based processing.

This is the Layer 5 (Rendering) MVP. The full mix chain with per-track
processing lives in ``yao.mix.mix_chain`` (Layer 5, Mix Chain).

This module uses only numpy — no pedalboard or pyloudnorm dependencies
(arch-lint: those libraries are restricted to mix/ and verify/ layers).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt
import structlog

from yao.schema.production import ProductionSpec

_NDFloat = npt.NDArray[np.floating[Any]]

logger = structlog.get_logger()


@dataclass(frozen=True)
class MixResult:
    """Result of mix chain processing.

    Attributes:
        audio: Processed audio array (stereo, float32).
        sample_rate: Sample rate in Hz.
        measured_lufs_approx: Approximate output LUFS (RMS-based).
        applied_reverb: Whether reverb was applied.
        applied_stereo_width: Whether stereo width was adjusted.
    """

    audio: _NDFloat
    sample_rate: int
    measured_lufs_approx: float
    applied_reverb: bool
    applied_stereo_width: bool


def apply_mix_chain(
    audio: _NDFloat,
    sample_rate: int,
    spec: ProductionSpec,
) -> MixResult:
    """Apply spec-driven mixing to rendered audio.

    Honors:
      - ``target_lufs``: RMS-based loudness normalization.
      - ``reverb_amount``: Simple convolution reverb (impulse response).
      - ``stereo_width``: Mid/Side stereo width adjustment.

    Args:
        audio: Input audio as numpy array (mono 1-D or stereo 2-D).
        sample_rate: Sample rate in Hz.
        spec: Production specification with mix parameters.

    Returns:
        MixResult with processed audio and metadata.
    """
    processed: _NDFloat = audio.astype(np.float64)
    applied_reverb = False
    applied_stereo_width = False

    # 1. Ensure stereo (2-D array with shape [samples, 2])
    if processed.ndim == 1:
        processed = np.column_stack([processed, processed])
    elif processed.ndim == 2 and processed.shape[1] == 1:
        processed = np.column_stack([processed[:, 0], processed[:, 0]])

    # 2. Apply reverb
    if spec.reverb_amount > 0.01:
        processed = _apply_simple_reverb(processed, sample_rate, spec.reverb_amount)
        applied_reverb = True

    # 3. Apply stereo width
    if abs(spec.stereo_width - 0.5) > 0.01:
        processed = _apply_stereo_width(processed, spec.stereo_width)
        applied_stereo_width = True

    # 4. Loudness normalization (RMS-based LUFS approximation)
    processed, measured_lufs = _normalize_loudness_rms(processed, spec.target_lufs)

    # 5. Final clip to prevent overs
    processed = np.clip(processed, -1.0, 1.0)

    result_audio: _NDFloat = processed.astype(np.float32)
    return MixResult(
        audio=result_audio,
        sample_rate=sample_rate,
        measured_lufs_approx=measured_lufs,
        applied_reverb=applied_reverb,
        applied_stereo_width=applied_stereo_width,
    )


def _apply_simple_reverb(
    audio: _NDFloat,
    sample_rate: int,
    amount: float,
) -> _NDFloat:
    """Apply simple delay-based reverb approximation.

    Uses a comb filter approach for efficiency. Not a true convolution
    reverb, but sufficient for preview/MVP purposes.

    Args:
        audio: Stereo audio [samples, 2].
        sample_rate: Sample rate.
        amount: Reverb amount (0.0-1.0).

    Returns:
        Audio with reverb applied.
    """
    # Three delay taps simulating early reflections
    delays_ms = [23.0, 47.0, 71.0]
    gains = [amount * 0.4, amount * 0.25, amount * 0.15]

    result = audio.copy()
    for delay_ms, gain in zip(delays_ms, gains, strict=True):
        delay_samples = int(sample_rate * delay_ms / 1000.0)
        if delay_samples >= len(audio):
            continue
        # Add delayed copy
        delayed = np.zeros_like(audio)
        delayed[delay_samples:] = audio[:-delay_samples] * gain
        result += delayed

    return result


def _apply_stereo_width(audio: _NDFloat, width: float) -> _NDFloat:
    """Adjust stereo width using Mid/Side processing.

    Args:
        audio: Stereo audio [samples, 2].
        width: Stereo width (0.0=mono, 0.5=unchanged, 1.0=full width).

    Returns:
        Width-adjusted audio.
    """
    left = audio[:, 0]
    right = audio[:, 1]

    mid = (left + right) * 0.5
    side = (left - right) * 0.5

    # width=0 → pure mono, width=1 → exaggerated stereo
    side_gain = width * 2.0  # 0→0, 0.5→1.0, 1.0→2.0

    new_left = mid + side * side_gain
    new_right = mid - side * side_gain

    return np.column_stack([new_left, new_right])


def _normalize_loudness_rms(
    audio: _NDFloat,
    target_lufs: float,
) -> tuple[_NDFloat, float]:
    """Normalize audio to approximate target LUFS using RMS.

    Args:
        audio: Audio array.
        target_lufs: Target loudness in LUFS (approximated as RMS dBFS).

    Returns:
        Tuple of (normalized audio, measured approximate LUFS).
    """
    rms = np.sqrt(np.mean(audio**2))
    if rms < 1e-10:
        return audio, -100.0

    current_db = 20.0 * np.log10(rms)
    gain_db = target_lufs - current_db
    gain_linear = 10.0 ** (gain_db / 20.0)

    normalized = audio * gain_linear
    new_rms = np.sqrt(np.mean(normalized**2))
    measured_lufs = 20.0 * np.log10(max(new_rms, 1e-10))

    return normalized, float(measured_lufs)
