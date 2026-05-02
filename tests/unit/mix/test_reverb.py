"""Tests for reverb processing."""

from __future__ import annotations

import numpy as np
import pytest

pedalboard = pytest.importorskip("pedalboard")

from yao.mix.reverb import apply_reverb  # noqa: E402
from yao.schema.production import ReverbSpec  # noqa: E402


@pytest.fixture()
def impulse() -> np.ndarray:
    """Short impulse signal — good for testing reverb tail."""
    sr = 44100
    y = np.zeros(sr, dtype=np.float32)
    y[0] = 1.0
    return y


class TestReverb:
    def test_adds_tail(self, impulse: np.ndarray) -> None:
        spec = ReverbSpec(type="hall", wet=0.5, decay_sec=1.0)
        result = apply_reverb(impulse, 44100, spec)
        # Reverb should add energy after the initial impulse
        tail_energy = float(np.sum(result[1000:] ** 2))
        assert tail_energy > 0

    def test_all_presets_work(self, impulse: np.ndarray) -> None:
        for preset in ("hall", "room", "plate", "spring"):
            spec = ReverbSpec(type=preset, wet=0.3)  # type: ignore[arg-type]
            result = apply_reverb(impulse, 44100, spec)
            assert len(result) == len(impulse)

    def test_dry_passthrough(self, impulse: np.ndarray) -> None:
        spec = ReverbSpec(wet=0.0)
        result = apply_reverb(impulse, 44100, spec)
        # With wet=0, output should be close to input
        correlation = float(np.corrcoef(impulse, result)[0, 1])
        assert correlation > 0.9

    def test_output_shape_preserved(self, impulse: np.ndarray) -> None:
        spec = ReverbSpec()
        result = apply_reverb(impulse, 44100, spec)
        assert result.shape == impulse.shape
