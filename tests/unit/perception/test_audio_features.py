"""Unit tests for AudioPerceptionAnalyzer and PerceptualReport."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from yao.perception.audio_features import (
    AudioPerceptionAnalyzer,
    AudioPerceptionError,
    BandName,
    PerceptualReport,
)

# ---------------------------------------------------------------------------
# Fixtures — generate minimal WAV files in tmp_path
# ---------------------------------------------------------------------------


@pytest.fixture()
def sine_wav(tmp_path: Path) -> Path:
    """1-second 440Hz sine wave at 44100 Hz, amplitude 0.5."""
    sr = 44100
    t = np.linspace(0.0, 1.0, sr, endpoint=False)
    y = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    path = tmp_path / "sine.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture()
def silence_wav(tmp_path: Path) -> Path:
    """0.5-second silence at 44100 Hz."""
    sr = 44100
    y = np.zeros(sr // 2, dtype=np.float32)
    path = tmp_path / "silence.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture()
def noise_wav(tmp_path: Path) -> Path:
    """2-second white noise at 44100 Hz, amplitude 0.3."""
    sr = 44100
    rng = np.random.default_rng(42)
    y = (0.3 * rng.standard_normal(sr * 2)).astype(np.float32)
    path = tmp_path / "noise.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture()
def analyzer() -> AudioPerceptionAnalyzer:
    """Fresh analyzer instance."""
    return AudioPerceptionAnalyzer()


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


class TestBasicAnalysis:
    def test_analyze_returns_frozen_report(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        assert isinstance(report, PerceptualReport)
        with pytest.raises(AttributeError):
            report.lufs_integrated = -10.0  # type: ignore[misc]

    def test_analyze_sine_produces_report(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        assert report.lufs_integrated < 0  # any real signal is negative LUFS
        assert len(report.lufs_short_term) >= 1
        assert report.spectral_centroid_mean > 0
        assert report.spectral_rolloff > 0

    def test_nonexistent_file_raises(self, analyzer: AudioPerceptionAnalyzer, tmp_path: Path) -> None:
        with pytest.raises(AudioPerceptionError, match="Failed to load"):
            analyzer.analyze(tmp_path / "does_not_exist.wav")


# ---------------------------------------------------------------------------
# Loudness (LUFS via pyloudnorm)
# ---------------------------------------------------------------------------


class TestLoudness:
    def test_lufs_sine_in_range(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        # 440Hz sine at 0.5 amplitude: LUFS somewhere around -9 to -3
        assert -20.0 < report.lufs_integrated < 0.0

    def test_peak_dbfs_below_zero(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        # amplitude 0.5 → peak ≈ -6 dBFS
        assert report.peak_dbfs < 0.0
        assert report.peak_dbfs > -12.0

    def test_silence_lufs_floor(self, analyzer: AudioPerceptionAnalyzer, silence_wav: Path) -> None:
        report = analyzer.analyze(silence_wav)
        # Silence should hit the -70 floor
        assert report.lufs_integrated <= -60.0

    def test_dynamic_range_non_negative(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        assert report.dynamic_range_db >= 0.0


# ---------------------------------------------------------------------------
# Spectral
# ---------------------------------------------------------------------------


class TestSpectral:
    def test_spectral_centroid_sine_near_440(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        # Pure sine at 440 Hz → centroid should be near 440
        assert 300 < report.spectral_centroid_mean < 600

    def test_spectral_flatness_noise_higher_than_sine(
        self,
        analyzer: AudioPerceptionAnalyzer,
        sine_wav: Path,
        noise_wav: Path,
    ) -> None:
        sine_report = analyzer.analyze(sine_wav)
        noise_report = analyzer.analyze(noise_wav)
        # White noise is spectrally flatter than a pure tone
        assert noise_report.spectral_flatness > sine_report.spectral_flatness

    def test_spectral_rolloff_positive(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        assert report.spectral_rolloff > 0


# ---------------------------------------------------------------------------
# Frequency bands
# ---------------------------------------------------------------------------


class TestBandEnergy:
    def test_all_bands_present(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        for band in BandName:
            assert band in report.frequency_band_energy

    def test_band_energies_sum_to_approximately_one(self, analyzer: AudioPerceptionAnalyzer, noise_wav: Path) -> None:
        report = analyzer.analyze(noise_wav)
        total = sum(report.frequency_band_energy.values())
        # Should sum close to 1.0 (normalized)
        assert 0.9 < total < 1.1

    def test_sine_energy_concentrated(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        # 440 Hz sine should have most energy in LOW_MID or MID band
        low_mid = report.frequency_band_energy[BandName.LOW_MID]
        mid = report.frequency_band_energy[BandName.MID]
        assert (low_mid + mid) > 0.5  # majority of energy


# ---------------------------------------------------------------------------
# Masking risk
# ---------------------------------------------------------------------------


class TestMaskingRisk:
    def test_masking_risk_in_range(self, analyzer: AudioPerceptionAnalyzer, noise_wav: Path) -> None:
        report = analyzer.analyze(noise_wav)
        assert 0.0 <= report.masking_risk_score <= 1.0

    def test_sine_low_masking(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        # Pure sine has energy in one band → low masking
        assert report.masking_risk_score < 0.5


# ---------------------------------------------------------------------------
# Rhythm
# ---------------------------------------------------------------------------


class TestRhythm:
    def test_onset_density_non_negative(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        for density in report.onset_density_per_section.values():
            assert density >= 0.0

    def test_tempo_stability_non_negative(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        assert report.tempo_stability_ms_drift >= 0.0


# ---------------------------------------------------------------------------
# Section boundaries
# ---------------------------------------------------------------------------


class TestSectionBoundaries:
    def test_section_keys_appear_in_report(self, analyzer: AudioPerceptionAnalyzer, noise_wav: Path) -> None:
        boundaries = {
            "intro": (0.0, 1.0),
            "main": (1.0, 2.0),
        }
        report = analyzer.analyze(noise_wav, section_boundaries=boundaries)
        assert "intro" in report.spectral_centroid_per_section
        assert "main" in report.spectral_centroid_per_section
        assert "intro" in report.onset_density_per_section
        assert "main" in report.onset_density_per_section

    def test_no_boundaries_uses_full(self, analyzer: AudioPerceptionAnalyzer, sine_wav: Path) -> None:
        report = analyzer.analyze(sine_wav)
        assert "full" in report.spectral_centroid_per_section
        assert "full" in report.onset_density_per_section
