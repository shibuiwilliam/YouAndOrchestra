"""Tests for EQ processing."""

from __future__ import annotations

import numpy as np
import pytest

pedalboard = pytest.importorskip("pedalboard")

from yao.mix.eq import apply_eq  # noqa: E402
from yao.schema.production import EQBand  # noqa: E402


@pytest.fixture()
def sine_100hz() -> np.ndarray:
    """1-second 100Hz sine wave at 44100Hz."""
    sr = 44100
    t = np.linspace(0.0, 1.0, sr, endpoint=False)
    return (0.5 * np.sin(2 * np.pi * 100 * t)).astype(np.float32)


class TestEQ:
    def test_highpass_reduces_low_freq(self, sine_100hz: np.ndarray) -> None:
        bands = [EQBand(freq=200.0, type="high_pass")]
        result = apply_eq(sine_100hz, 44100, bands)
        # High-pass at 200Hz should reduce 100Hz energy
        original_energy = float(np.sum(sine_100hz**2))
        result_energy = float(np.sum(result**2))
        assert result_energy < original_energy * 0.5

    def test_empty_bands_passthrough(self, sine_100hz: np.ndarray) -> None:
        result = apply_eq(sine_100hz, 44100, [])
        np.testing.assert_array_equal(result, sine_100hz)

    def test_peak_boost(self, sine_100hz: np.ndarray) -> None:
        bands = [EQBand(freq=100.0, gain=6.0, q=1.0, type="peak")]
        result = apply_eq(sine_100hz, 44100, bands)
        assert float(np.max(np.abs(result))) > float(np.max(np.abs(sine_100hz)))

    def test_output_shape_preserved(self, sine_100hz: np.ndarray) -> None:
        bands = [EQBand(freq=1000.0, type="high_pass")]
        result = apply_eq(sine_100hz, 44100, bands)
        assert result.shape == sine_100hz.shape
