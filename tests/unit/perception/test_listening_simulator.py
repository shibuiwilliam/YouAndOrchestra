"""Tests for the Listening Simulator (Step 7.5)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from yao.perception.audio_features import PerceptualReport
from yao.perception.listening_simulator import ListeningResult, ListeningSimulator
from yao.schema.intent import IntentSpec

# ---------------------------------------------------------------------------
# Fixtures
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
def busy_wav(tmp_path: Path) -> Path:
    """2-second busy signal (many transients) for testing onset density."""
    sr = 44100
    duration = 2.0
    n_samples = int(sr * duration)
    rng = np.random.default_rng(42)
    # Create clicks every 50ms to generate high onset density
    y = np.zeros(n_samples, dtype=np.float32)
    click_interval = int(0.05 * sr)
    for i in range(0, n_samples, click_interval):
        end = min(i + 100, n_samples)
        y[i:end] = 0.8 * rng.standard_normal(end - i).astype(np.float32)
    path = tmp_path / "busy.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture()
def simulator() -> ListeningSimulator:
    """Fresh ListeningSimulator instance."""
    return ListeningSimulator()


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


class TestListeningSimulatorBasic:
    def test_simulate_returns_listening_result(self, simulator: ListeningSimulator, sine_wav: Path) -> None:
        result = simulator.simulate(sine_wav)
        assert isinstance(result, ListeningResult)
        assert isinstance(result.report, PerceptualReport)

    def test_simulate_persists_perceptual_json(
        self, simulator: ListeningSimulator, sine_wav: Path, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "output"
        result = simulator.simulate(sine_wav, output_dir=output_dir)
        assert result.perceptual_json_path is not None
        assert result.perceptual_json_path.exists()
        assert result.perceptual_json_path.name == "perceptual.json"

    def test_simulate_no_output_dir_skips_persistence(self, simulator: ListeningSimulator, sine_wav: Path) -> None:
        result = simulator.simulate(sine_wav, output_dir=None)
        assert result.perceptual_json_path is None

    def test_perceptual_json_is_valid_json(self, simulator: ListeningSimulator, sine_wav: Path, tmp_path: Path) -> None:
        import json

        output_dir = tmp_path / "output"
        result = simulator.simulate(sine_wav, output_dir=output_dir)
        assert result.perceptual_json_path is not None
        data = json.loads(result.perceptual_json_path.read_text())
        assert "lufs_integrated" in data
        assert "spectral_centroid_mean" in data
        assert "frequency_band_energy" in data

    def test_section_boundaries_passed_through(self, simulator: ListeningSimulator, sine_wav: Path) -> None:
        boundaries = {"part_a": (0.0, 0.5), "part_b": (0.5, 1.0)}
        result = simulator.simulate(sine_wav, section_boundaries=boundaries)
        assert "part_a" in result.report.onset_density_per_section
        assert "part_b" in result.report.onset_density_per_section


# ---------------------------------------------------------------------------
# Mood divergence detection
# ---------------------------------------------------------------------------


class TestMoodDivergence:
    def test_no_divergence_when_no_intent(self, simulator: ListeningSimulator, sine_wav: Path) -> None:
        result = simulator.simulate(sine_wav, intent=None)
        assert not result.has_divergence

    def test_no_divergence_for_matching_mood(self, simulator: ListeningSimulator, sine_wav: Path) -> None:
        # A pure sine wave is dark (low spectral centroid around 440Hz)
        # Use a keyword that checks spectral centroid (not onset density,
        # since librosa may detect spurious onsets in pure tones).
        intent = IntentSpec(text="A dark melancholy piece", keywords=["dark"])
        result = simulator.simulate(sine_wav, intent=intent)
        # Sine at 440Hz has centroid < 2500Hz → matches "dark" expectation
        assert not result.has_divergence

    def test_divergence_detected_for_busy_calm_mismatch(self, simulator: ListeningSimulator, busy_wav: Path) -> None:
        # Busy signal but intent says "calm"
        intent = IntentSpec(text="A calm peaceful melody", keywords=["calm", "peaceful"])
        result = simulator.simulate(busy_wav, intent=intent)
        # Busy WAV should have high onset density, violating "calm" expectation
        assert result.has_divergence
        # Check divergence tuple structure
        for keyword, metric, expected, actual in result.mood_divergences:
            assert isinstance(keyword, str)
            assert isinstance(metric, str)
            assert isinstance(expected, float)
            assert isinstance(actual, float)

    def test_divergence_includes_keyword_info(self, simulator: ListeningSimulator, busy_wav: Path) -> None:
        intent = IntentSpec(text="calm", keywords=["calm"])
        result = simulator.simulate(busy_wav, intent=intent)
        if result.has_divergence:
            keywords_found = {d[0] for d in result.mood_divergences}
            assert "calm" in keywords_found

    def test_unknown_keywords_ignored(self, simulator: ListeningSimulator, sine_wav: Path) -> None:
        intent = IntentSpec(text="A xyzzy piece", keywords=["xyzzy"])
        result = simulator.simulate(sine_wav, intent=intent)
        assert not result.has_divergence
