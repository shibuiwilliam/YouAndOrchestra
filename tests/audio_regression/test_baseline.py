"""Audio regression baseline tests.

Renders synthetic test signals with known acoustic properties and
verifies that PerceptualReport extraction produces stable results.

These serve as the audio regression foundation. Real piece baselines
are added incrementally as the generation pipeline matures.

Marked ``audio_regression`` — run via ``make test-acoustic`` or weekly CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from yao.perception.audio_features import AudioPerceptionAnalyzer
from yao.perception.listening_simulator import ListeningSimulator

# ---------------------------------------------------------------------------
# Synthetic test signals with known properties
# ---------------------------------------------------------------------------

_SR = 44100
_BASELINES_DIR = Path(__file__).parent / "baselines"


def _generate_reference_sine(tmp_path: Path) -> Path:
    """Generate a 3-second 1kHz sine wave at -6 dBFS (amplitude 0.5)."""
    duration = 3.0
    t = np.linspace(0.0, duration, int(_SR * duration), endpoint=False)
    y = (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    path = tmp_path / "ref_sine_1khz.wav"
    sf.write(str(path), y, _SR)
    return path


def _generate_reference_noise(tmp_path: Path) -> Path:
    """Generate 3-second white noise at -12 dBFS (amplitude 0.25)."""
    duration = 3.0
    rng = np.random.default_rng(12345)
    y = (0.25 * rng.standard_normal(int(_SR * duration))).astype(np.float32)
    path = tmp_path / "ref_noise.wav"
    sf.write(str(path), y, _SR)
    return path


def _generate_two_section_signal(tmp_path: Path) -> Path:
    """Generate a signal with a quiet section and a loud section."""
    duration_each = 3.0
    n = int(_SR * duration_each)
    t = np.linspace(0.0, duration_each, n, endpoint=False)
    quiet = (0.1 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    loud = (0.7 * np.sin(2 * np.pi * 880 * t)).astype(np.float32)
    y = np.concatenate([quiet, loud])
    path = tmp_path / "two_sections.wav"
    sf.write(str(path), y, _SR)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.audio_regression
class TestSyntheticBaselines:
    """Verify that feature extraction produces known results for reference signals."""

    def test_sine_1khz_spectral_centroid(self, tmp_path: Path) -> None:
        """1kHz sine should have spectral centroid near 1000Hz."""
        wav_path = _generate_reference_sine(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        report = analyzer.analyze(wav_path)
        # Spectral centroid of a pure sine is at the sine's frequency
        assert 800.0 < report.spectral_centroid_mean < 1200.0

    def test_sine_1khz_lufs_approximate(self, tmp_path: Path) -> None:
        """1kHz sine at 0.5 amplitude should be approximately -9 to -4 LUFS."""
        wav_path = _generate_reference_sine(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        report = analyzer.analyze(wav_path)
        # Sine at amplitude 0.5 → approximately -6 dBFS → LUFS around -9 to -4
        assert -12.0 < report.lufs_integrated < -2.0

    def test_sine_1khz_peak_dbfs(self, tmp_path: Path) -> None:
        """Peak for amplitude 0.5 should be near -6 dBFS."""
        wav_path = _generate_reference_sine(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        report = analyzer.analyze(wav_path)
        assert -7.5 < report.peak_dbfs < -5.0

    def test_noise_high_spectral_flatness(self, tmp_path: Path) -> None:
        """White noise should have high spectral flatness."""
        wav_path = _generate_reference_noise(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        report = analyzer.analyze(wav_path)
        assert report.spectral_flatness > 0.3

    def test_noise_bands_distributed(self, tmp_path: Path) -> None:
        """White noise should have energy in multiple bands (not just one)."""
        wav_path = _generate_reference_noise(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        report = analyzer.analyze(wav_path)
        energies = list(report.frequency_band_energy.values())
        # At least 3 bands should have >1% energy (noise spreads)
        significant_bands = sum(1 for e in energies if e > 0.01)
        assert significant_bands >= 3

    def test_two_section_dynamic_range(self, tmp_path: Path) -> None:
        """Quiet+loud signal should have measurable dynamic range."""
        wav_path = _generate_two_section_signal(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        report = analyzer.analyze(wav_path)
        assert report.dynamic_range_db > 3.0

    def test_listening_simulator_persists_json(self, tmp_path: Path) -> None:
        """ListeningSimulator creates perceptual.json with correct keys."""
        wav_path = _generate_reference_sine(tmp_path)
        output_dir = tmp_path / "output"
        simulator = ListeningSimulator()
        result = simulator.simulate(wav_path, output_dir=output_dir)
        assert result.perceptual_json_path is not None
        data = json.loads(result.perceptual_json_path.read_text())
        required_keys = [
            "lufs_integrated",
            "spectral_centroid_mean",
            "spectral_rolloff",
            "spectral_flatness",
            "frequency_band_energy",
            "masking_risk_score",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"


@pytest.mark.audio_regression
class TestFeatureStability:
    """Verify that repeated extraction of the same file produces identical results."""

    def test_deterministic_extraction(self, tmp_path: Path) -> None:
        """Same input should yield identical PerceptualReport."""
        wav_path = _generate_reference_sine(tmp_path)
        analyzer = AudioPerceptionAnalyzer()
        r1 = analyzer.analyze(wav_path)
        r2 = analyzer.analyze(wav_path)
        assert r1.lufs_integrated == r2.lufs_integrated
        assert r1.spectral_centroid_mean == r2.spectral_centroid_mean
        assert r1.spectral_flatness == r2.spectral_flatness
        assert r1.masking_risk_score == r2.masking_risk_score
