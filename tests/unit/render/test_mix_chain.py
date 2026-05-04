"""Tests for the simple spec-driven mix chain MVP."""

from __future__ import annotations

import numpy as np
import pytest

from yao.render.mix_chain import MixResult, apply_mix_chain
from yao.schema.production import ProductionSpec


def _sine_audio(freq: float = 440.0, duration: float = 1.0, sr: int = 44100) -> np.ndarray:
    """Generate a test sine wave."""
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)
    return (0.5 * np.sin(2.0 * np.pi * freq * t)).astype(np.float32)


class TestApplyMixChain:
    """Test the mix chain processor."""

    def test_returns_mix_result(self) -> None:
        """apply_mix_chain returns a MixResult."""
        audio = _sine_audio()
        spec = ProductionSpec()
        result = apply_mix_chain(audio, 44100, spec)
        assert isinstance(result, MixResult)
        assert result.sample_rate == 44100

    def test_output_is_stereo(self) -> None:
        """Output should always be stereo (N, 2)."""
        audio = _sine_audio()  # mono
        spec = ProductionSpec()
        result = apply_mix_chain(audio, 44100, spec)
        assert result.audio.ndim == 2  # noqa: PLR2004
        assert result.audio.shape[1] == 2  # noqa: PLR2004

    def test_target_lufs_normalization(self) -> None:
        """Output LUFS should approximate the target."""
        audio = _sine_audio()
        spec = ProductionSpec(target_lufs=-14.0)
        result = apply_mix_chain(audio, 44100, spec)
        # RMS approximation — within 1 dB is acceptable for MVP
        assert abs(result.measured_lufs_approx - (-14.0)) < 1.0

    def test_different_lufs_targets_produce_different_levels(self) -> None:
        """Two different LUFS targets should produce different output levels."""
        audio = _sine_audio()
        result_loud = apply_mix_chain(audio, 44100, ProductionSpec(target_lufs=-10.0))
        result_quiet = apply_mix_chain(audio, 44100, ProductionSpec(target_lufs=-20.0))
        rms_loud = np.sqrt(np.mean(result_loud.audio**2))
        rms_quiet = np.sqrt(np.mean(result_quiet.audio**2))
        assert rms_loud > rms_quiet

    def test_reverb_applied_when_nonzero(self) -> None:
        """Reverb flag should be True when reverb_amount > 0."""
        audio = _sine_audio()
        spec = ProductionSpec(reverb_amount=0.5)
        result = apply_mix_chain(audio, 44100, spec)
        assert result.applied_reverb is True

    def test_no_reverb_when_zero(self) -> None:
        """Reverb flag should be False when reverb_amount is 0."""
        audio = _sine_audio()
        spec = ProductionSpec(reverb_amount=0.0)
        result = apply_mix_chain(audio, 44100, spec)
        assert result.applied_reverb is False

    def test_stereo_width_applied(self) -> None:
        """Stereo width processing should be flagged when non-default."""
        audio = _sine_audio()
        spec = ProductionSpec(stereo_width=1.0)
        result = apply_mix_chain(audio, 44100, spec)
        assert result.applied_stereo_width is True

    def test_stereo_width_mono(self) -> None:
        """Width 0.0 should produce near-mono output."""
        # Create stereo input with different L/R
        sr = 44100
        t = np.linspace(0, 1.0, sr, dtype=np.float32)
        left = 0.5 * np.sin(2.0 * np.pi * 440.0 * t)
        right = 0.5 * np.sin(2.0 * np.pi * 660.0 * t)
        stereo = np.column_stack([left, right]).astype(np.float32)

        spec = ProductionSpec(stereo_width=0.0)
        result = apply_mix_chain(stereo, sr, spec)
        # L and R should be identical (mono)
        np.testing.assert_allclose(
            result.audio[:, 0],
            result.audio[:, 1],
            atol=0.01,
        )

    def test_silent_audio_handled(self) -> None:
        """Silent audio should not crash."""
        audio = np.zeros(44100, dtype=np.float32)
        spec = ProductionSpec()
        result = apply_mix_chain(audio, 44100, spec)
        assert result.measured_lufs_approx == pytest.approx(-100.0)

    def test_output_clipped_to_minus_one_plus_one(self) -> None:
        """Output must not exceed [-1, 1]."""
        audio = _sine_audio()
        spec = ProductionSpec(target_lufs=-5.0)  # loud target
        result = apply_mix_chain(audio, 44100, spec)
        assert np.max(result.audio) <= 1.0
        assert np.min(result.audio) >= -1.0
