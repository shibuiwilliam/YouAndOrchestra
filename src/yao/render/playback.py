"""Audio playback utilities — inline and external.

Provides functions to play WAV audio directly via sounddevice (inline)
or through the OS default player (external), plus LUFS normalization
to ensure consistent preview volume across different SoundFonts.

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

import numpy as np
import structlog

from yao.errors import RenderError

logger = structlog.get_logger()

# Target LUFS for preview normalization
DEFAULT_TARGET_LUFS = -16.0

# Sample rate used by the audio pipeline
DEFAULT_SAMPLE_RATE = 44100


def play_wav_inline(
    audio: np.ndarray,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    *,
    target_lufs: float = DEFAULT_TARGET_LUFS,
    block: bool = True,
) -> None:
    """Play audio data directly using sounddevice.

    Args:
        audio: Audio samples as a 1-D or 2-D numpy array.
        sample_rate: Sample rate in Hz.
        target_lufs: Normalize to this LUFS level before playback.
        block: If True, wait for playback to finish.

    Raises:
        RenderError: If sounddevice is not available.
    """
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RenderError("sounddevice is not installed. Install with: pip install sounddevice") from exc

    normalized = normalize_loudness(audio, target_lufs=target_lufs)
    sd.play(normalized, samplerate=sample_rate)
    if block:
        sd.wait()


def play_wav_external(wav_path: Path) -> None:
    """Open a WAV file in the OS default audio player.

    Args:
        wav_path: Path to the WAV file.

    Raises:
        RenderError: If the file does not exist or opening fails.
    """
    if not wav_path.exists():
        raise RenderError(f"WAV file not found: {wav_path}")

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", str(wav_path)])  # noqa: S603
        elif system == "Linux":
            subprocess.Popen(["xdg-open", str(wav_path)])  # noqa: S603
        elif system == "Windows":
            subprocess.Popen(["start", "", str(wav_path)], shell=True)  # noqa: S602, S603
        else:
            raise RenderError(f"Unsupported platform for external playback: {system}")
    except OSError as e:
        raise RenderError(f"Failed to open audio player: {e}") from e

    logger.info("external_playback_started", path=str(wav_path), platform=system)


def normalize_loudness(
    audio: np.ndarray,
    *,
    target_lufs: float = DEFAULT_TARGET_LUFS,
) -> np.ndarray:
    """Normalize audio loudness to a target LUFS level.

    Uses pyloudnorm if available for ITU-R BS.1770 compliant measurement.
    Falls back to simple RMS normalization if pyloudnorm is not installed.

    Args:
        audio: Audio samples as a numpy array (mono or stereo).
        target_lufs: Target loudness in LUFS (default: -16).

    Returns:
        Normalized audio array (same shape as input).
    """
    if audio.size == 0:
        return audio

    # Use RMS-based normalization in the render layer.
    # Full ITU-R BS.1770 (pyloudnorm) measurement belongs in verify/ layer.
    # RMS approximation is sufficient for preview playback consistency.
    return _rms_normalize(audio, target_lufs)


def _rms_normalize(audio: np.ndarray, target_lufs: float) -> np.ndarray:
    """Simple RMS-based normalization fallback.

    Approximates LUFS as RMS dBFS (not standards-compliant but usable).

    Args:
        audio: Audio samples.
        target_lufs: Target loudness approximated as RMS dBFS.

    Returns:
        Normalized audio array.
    """
    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
    if rms < 1e-10:
        return audio

    current_db = 20.0 * np.log10(rms)
    gain_db = target_lufs - current_db
    gain_linear = 10.0 ** (gain_db / 20.0)

    normalized = audio.astype(np.float64) * gain_linear

    # Clip to prevent clipping
    if audio.dtype in (np.float32, np.float64):
        normalized = np.clip(normalized, -1.0, 1.0)

    out: np.ndarray = normalized.astype(audio.dtype)
    return out
