"""Tests for master chain processing."""

from __future__ import annotations

import warnings

import numpy as np
import pyloudnorm
import pytest

pedalboard = pytest.importorskip("pedalboard")

from yao.mix.master_chain import apply_master  # noqa: E402
from yao.schema.production import CompressionSpec, MasterSpec  # noqa: E402


@pytest.fixture()
def stereo_signal() -> np.ndarray:
    """2-second stereo sine wave (amplitude 0.7)."""
    sr = 44100
    t = np.linspace(0.0, 2.0, sr * 2, endpoint=False)
    mono = (0.7 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    return np.column_stack([mono, mono])


class TestMasterChain:
    def test_lufs_near_target(self, stereo_signal: np.ndarray) -> None:
        spec = MasterSpec(target_lufs=-14.0, true_peak_max_dbfs=-1.0)
        result = apply_master(stereo_signal, 44100, spec)

        meter = pyloudnorm.Meter(44100)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            measured_lufs = meter.integrated_loudness(result.astype(np.float64))

        # Should be within ±2 dB of target
        assert abs(measured_lufs - (-14.0)) < 2.0, f"Expected LUFS near -14.0, got {measured_lufs:.1f}"

    def test_true_peak_limited(self, stereo_signal: np.ndarray) -> None:
        spec = MasterSpec(true_peak_max_dbfs=-1.0)
        result = apply_master(stereo_signal, 44100, spec)

        peak_db = float(20.0 * np.log10(max(float(np.max(np.abs(result))), 1e-10)))
        # Peak should not significantly exceed the limit
        assert peak_db < 0.0

    def test_with_master_compression(self, stereo_signal: np.ndarray) -> None:
        spec = MasterSpec(
            target_lufs=-14.0,
            compression=CompressionSpec(threshold_db=-10.0, ratio=3.0),
        )
        result = apply_master(stereo_signal, 44100, spec)
        assert result.shape == stereo_signal.shape

    def test_output_shape_preserved(self, stereo_signal: np.ndarray) -> None:
        spec = MasterSpec()
        result = apply_master(stereo_signal, 44100, spec)
        assert result.shape == stereo_signal.shape
