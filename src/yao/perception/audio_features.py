"""Audio Perception Stage 1 — feature extraction from rendered audio.

Extracts objective audio features using ``librosa`` and ``pyloudnorm``.
These feed into the Perception Substitute Layer (Layer 4), enabling
the Conductor to "hear" what the generators produced.

**Rules (CLAUDE.md Tier 1)**:
- All ``librosa`` calls live in THIS file only.
- Sample rate: ``librosa.load(..., sr=None)`` to preserve original.
- LUFS: ``pyloudnorm.Meter`` only — no RMS approximation.
- ``PerceptualReport`` is frozen; one analysis = one report.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import numpy.typing as npt
import pyloudnorm

from yao.errors import YaOError

# Shorthand for numpy array type used throughout this module.
_NDFloat = npt.NDArray[np.floating[Any]]

# ---------------------------------------------------------------------------
# BandName — frequency band categories
# ---------------------------------------------------------------------------


class BandName(Enum):
    """Standard frequency band names for mix analysis."""

    SUB_BASS = "sub_bass"  # 20-60 Hz
    BASS = "bass"  # 60-250 Hz
    LOW_MID = "low_mid"  # 250-500 Hz
    MID = "mid"  # 500-2000 Hz
    HIGH_MID = "high_mid"  # 2000-4000 Hz
    PRESENCE = "presence"  # 4000-6000 Hz
    BRILLIANCE = "brilliance"  # 6000-20000 Hz


_BAND_RANGES: dict[BandName, tuple[float, float]] = {
    BandName.SUB_BASS: (20.0, 60.0),
    BandName.BASS: (60.0, 250.0),
    BandName.LOW_MID: (250.0, 500.0),
    BandName.MID: (500.0, 2000.0),
    BandName.HIGH_MID: (2000.0, 4000.0),
    BandName.PRESENCE: (4000.0, 6000.0),
    BandName.BRILLIANCE: (6000.0, 20000.0),
}


# ---------------------------------------------------------------------------
# PerceptualReport — frozen output
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerceptualReport:
    """Complete audio perception analysis result.

    Produced by ``AudioPerceptionAnalyzer.analyze()``. Frozen and immutable.
    One analysis run = one report instance.

    Attributes:
        lufs_integrated: Integrated loudness in LUFS.
        lufs_short_term: Sequence of (time_sec, lufs) for 3-second windows.
        peak_dbfs: Peak amplitude in dBFS.
        dynamic_range_db: Difference between loudest and quietest short-term LUFS.
        spectral_centroid_mean: Mean spectral centroid in Hz.
        spectral_centroid_per_section: Per-section mean spectral centroid.
        spectral_rolloff: Frequency below which 85% of spectral energy lies.
        spectral_flatness: Mean spectral flatness [0, 1]. 1.0 = white noise.
        onset_density_per_section: Onsets per second, per section.
        tempo_stability_ms_drift: Standard deviation of beat intervals in ms.
        frequency_band_energy: Normalized energy per frequency band.
        masking_risk_score: Fraction of adjacent band pairs with high overlap [0, 1].
    """

    lufs_integrated: float
    lufs_short_term: tuple[tuple[float, float], ...]
    peak_dbfs: float
    dynamic_range_db: float
    spectral_centroid_mean: float
    spectral_centroid_per_section: dict[str, float]
    spectral_rolloff: float
    spectral_flatness: float
    onset_density_per_section: dict[str, float]
    tempo_stability_ms_drift: float
    frequency_band_energy: dict[BandName, float]
    masking_risk_score: float


class AudioPerceptionError(YaOError):
    """Raised when audio perception analysis fails."""


# ---------------------------------------------------------------------------
# AudioPerceptionAnalyzer
# ---------------------------------------------------------------------------


class AudioPerceptionAnalyzer:
    """Extracts audio features from a WAV file.

    This is the sole entry point for audio analysis in YaO.
    All librosa and pyloudnorm calls are encapsulated here.
    """

    def analyze(
        self,
        audio_path: Path,
        section_boundaries: dict[str, tuple[float, float]] | None = None,
    ) -> PerceptualReport:
        """Analyze an audio file and produce a frozen PerceptualReport.

        Args:
            audio_path: Path to a WAV file.
            section_boundaries: Optional mapping from section name to
                (start_sec, end_sec). Used for per-section metrics.
                If None, the entire file is treated as one section named "full".

        Returns:
            Frozen PerceptualReport with all extracted features.

        Raises:
            AudioPerceptionError: If the file cannot be loaded or analyzed.
        """
        try:
            y, sr_raw = librosa.load(str(audio_path), sr=None)
        except Exception as e:
            raise AudioPerceptionError(f"Failed to load audio from {audio_path}: {e}") from e

        if len(y) == 0:
            raise AudioPerceptionError(f"Audio file is empty: {audio_path}")

        sr: int = int(sr_raw)
        y_float = y.astype(np.float64)

        if section_boundaries is None:
            duration = len(y) / sr
            section_boundaries = {"full": (0.0, duration)}

        # --- Loudness ---
        lufs_integrated = self._compute_lufs_integrated(y_float, sr)
        lufs_short_term = self._compute_lufs_short_term(y_float, sr)
        peak_dbfs = self._compute_peak_dbfs(y_float)
        dynamic_range_db = self._compute_dynamic_range(lufs_short_term)

        # --- Spectral ---
        spectral_centroid_mean = self._compute_spectral_centroid_mean(y, sr)
        spectral_centroid_per_section = self._compute_spectral_centroid_per_section(y, sr, section_boundaries)
        spectral_rolloff = self._compute_spectral_rolloff(y, sr)
        spectral_flatness = self._compute_spectral_flatness(y)

        # --- Rhythm ---
        onset_density_per_section = self._compute_onset_density_per_section(y, sr, section_boundaries)
        tempo_stability_ms_drift = self._compute_tempo_stability(y, sr)

        # --- Frequency bands ---
        frequency_band_energy = self._compute_band_energy(y, sr)
        masking_risk_score = self._compute_masking_risk(frequency_band_energy)

        return PerceptualReport(
            lufs_integrated=lufs_integrated,
            lufs_short_term=tuple(lufs_short_term),
            peak_dbfs=peak_dbfs,
            dynamic_range_db=dynamic_range_db,
            spectral_centroid_mean=spectral_centroid_mean,
            spectral_centroid_per_section=spectral_centroid_per_section,
            spectral_rolloff=spectral_rolloff,
            spectral_flatness=spectral_flatness,
            onset_density_per_section=onset_density_per_section,
            tempo_stability_ms_drift=tempo_stability_ms_drift,
            frequency_band_energy=frequency_band_energy,
            masking_risk_score=masking_risk_score,
        )

    # ------------------------------------------------------------------
    # Loudness
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_lufs_integrated(y: _NDFloat, sr: int) -> float:
        """Compute integrated LUFS using pyloudnorm.Meter."""
        meter = pyloudnorm.Meter(sr)
        # pyloudnorm expects shape (samples,) or (samples, channels)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lufs: float = meter.integrated_loudness(y)
        if np.isinf(lufs) or np.isnan(lufs):
            return -70.0  # silence floor
        return float(lufs)

    @staticmethod
    def _compute_lufs_short_term(
        y: _NDFloat,
        sr: int,
        window_sec: float = 3.0,
        hop_sec: float = 1.0,
    ) -> list[tuple[float, float]]:
        """Compute short-term LUFS over sliding windows."""
        meter = pyloudnorm.Meter(sr)
        window_samples = int(window_sec * sr)
        hop_samples = int(hop_sec * sr)

        if len(y) < window_samples:
            lufs = meter.integrated_loudness(y)
            val = -70.0 if (np.isinf(lufs) or np.isnan(lufs)) else float(lufs)
            return [(0.0, val)]

        results: list[tuple[float, float]] = []
        pos = 0
        while pos + window_samples <= len(y):
            chunk = y[pos : pos + window_samples]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                lufs = meter.integrated_loudness(chunk)
            val = -70.0 if (np.isinf(lufs) or np.isnan(lufs)) else float(lufs)
            time_sec = pos / sr
            results.append((round(time_sec, 3), round(val, 2)))
            pos += hop_samples

        return results

    @staticmethod
    def _compute_peak_dbfs(y: _NDFloat) -> float:
        """Compute peak amplitude in dBFS."""
        peak = float(np.max(np.abs(y)))
        if peak <= 0:
            return -96.0
        return float(20.0 * np.log10(peak))

    @staticmethod
    def _compute_dynamic_range(
        lufs_short_term: list[tuple[float, float]],
    ) -> float:
        """Compute dynamic range from short-term LUFS values."""
        if not lufs_short_term:
            return 0.0
        values = [v for _, v in lufs_short_term if v > -70.0]
        if len(values) < 2:
            return 0.0
        return float(max(values) - min(values))

    # ------------------------------------------------------------------
    # Spectral
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_spectral_centroid_mean(y: _NDFloat, sr: int) -> float:
        """Compute mean spectral centroid in Hz."""
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        return float(np.mean(centroid))

    @staticmethod
    def _compute_spectral_centroid_per_section(
        y: _NDFloat,
        sr: int,
        section_boundaries: dict[str, tuple[float, float]],
    ) -> dict[str, float]:
        """Compute mean spectral centroid per section."""
        result: dict[str, float] = {}
        for name, (start, end) in section_boundaries.items():
            start_sample = int(start * sr)
            end_sample = min(int(end * sr), len(y))
            if end_sample <= start_sample:
                result[name] = 0.0
                continue
            segment = y[start_sample:end_sample]
            centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)
            result[name] = float(np.mean(centroid))
        return result

    @staticmethod
    def _compute_spectral_rolloff(y: _NDFloat, sr: int) -> float:
        """Compute spectral rolloff (85% energy threshold) in Hz."""
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
        return float(np.mean(rolloff))

    @staticmethod
    def _compute_spectral_flatness(y: _NDFloat) -> float:
        """Compute mean spectral flatness [0, 1]."""
        flatness = librosa.feature.spectral_flatness(y=y)
        return float(np.mean(flatness))

    # ------------------------------------------------------------------
    # Rhythm
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_onset_density_per_section(
        y: _NDFloat,
        sr: int,
        section_boundaries: dict[str, tuple[float, float]],
    ) -> dict[str, float]:
        """Compute onset density (onsets/sec) per section."""
        result: dict[str, float] = {}
        for name, (start, end) in section_boundaries.items():
            start_sample = int(start * sr)
            end_sample = min(int(end * sr), len(y))
            duration = (end_sample - start_sample) / sr
            if duration <= 0:
                result[name] = 0.0
                continue
            segment = y[start_sample:end_sample]
            onsets = librosa.onset.onset_detect(y=segment, sr=sr, units="time")
            result[name] = float(len(onsets) / duration)
        return result

    @staticmethod
    def _compute_tempo_stability(y: _NDFloat, sr: int) -> float:
        """Compute tempo stability as std of beat intervals in milliseconds."""
        _tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        if len(beat_frames) < 2:
            return 0.0
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        intervals_ms = np.diff(beat_times) * 1000.0
        return float(np.std(intervals_ms))

    # ------------------------------------------------------------------
    # Frequency bands
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_band_energy(
        y: _NDFloat,
        sr: int,
    ) -> dict[BandName, float]:
        """Compute normalized energy per frequency band."""
        stft = np.abs(librosa.stft(y=y))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

        band_energies: dict[BandName, float] = {}
        total_energy = float(np.sum(stft**2))
        if total_energy <= 0:
            return {band: 0.0 for band in BandName}

        for band, (lo, hi) in _BAND_RANGES.items():
            mask = (freqs >= lo) & (freqs < hi)
            band_stft = stft[mask, :] if np.any(mask) else np.zeros((1, stft.shape[1]))
            energy = float(np.sum(band_stft**2))
            band_energies[band] = energy / total_energy

        return band_energies

    @staticmethod
    def _compute_masking_risk(
        band_energy: dict[BandName, float],
        threshold: float = 0.8,
    ) -> float:
        """Compute masking risk as fraction of adjacent band pairs with high overlap.

        Two adjacent bands "mask" if their energy ratio is close to 1:1
        (both dominant in overlapping range). Risk is the fraction of
        adjacent pairs where min/max > threshold.

        Args:
            band_energy: Per-band energy from ``_compute_band_energy``.
            threshold: Ratio threshold for masking detection.

        Returns:
            Score in [0.0, 1.0]. 0.0 = no masking, 1.0 = all bands mask.
        """
        bands = list(BandName)
        if len(bands) < 2:
            return 0.0

        masking_count = 0
        pair_count = 0
        for i in range(len(bands) - 1):
            e1 = band_energy.get(bands[i], 0.0)
            e2 = band_energy.get(bands[i + 1], 0.0)
            pair_count += 1
            if e1 <= 0 or e2 <= 0:
                continue
            ratio = min(e1, e2) / max(e1, e2)
            if ratio > threshold:
                masking_count += 1

        return masking_count / pair_count if pair_count > 0 else 0.0
