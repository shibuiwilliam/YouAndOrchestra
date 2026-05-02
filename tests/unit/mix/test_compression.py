"""Tests for compression processing."""

from __future__ import annotations

import numpy as np
import pytest

pedalboard = pytest.importorskip("pedalboard")

from yao.mix.compression import apply_compression  # noqa: E402
from yao.schema.production import CompressionSpec  # noqa: E402


@pytest.fixture()
def loud_signal() -> np.ndarray:
    """1-second loud sine wave (amplitude 0.9)."""
    sr = 44100
    t = np.linspace(0.0, 1.0, sr, endpoint=False)
    return (0.9 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


class TestCompression:
    def test_reduces_peak(self, loud_signal: np.ndarray) -> None:
        spec = CompressionSpec(threshold_db=-6.0, ratio=4.0)
        result = apply_compression(loud_signal, 44100, spec)
        original_peak = float(np.max(np.abs(loud_signal)))
        result_peak = float(np.max(np.abs(result)))
        assert result_peak <= original_peak

    def test_output_shape_preserved(self, loud_signal: np.ndarray) -> None:
        spec = CompressionSpec()
        result = apply_compression(loud_signal, 44100, spec)
        assert result.shape == loud_signal.shape

    def test_light_compression_less_change(self, loud_signal: np.ndarray) -> None:
        light = CompressionSpec(threshold_db=-3.0, ratio=1.5)
        heavy = CompressionSpec(threshold_db=-20.0, ratio=8.0)
        result_light = apply_compression(loud_signal, 44100, light)
        result_heavy = apply_compression(loud_signal, 44100, heavy)
        # Heavy compression should reduce RMS more
        rms_light = float(np.sqrt(np.mean(result_light**2)))
        rms_heavy = float(np.sqrt(np.mean(result_heavy**2)))
        assert rms_heavy <= rms_light
