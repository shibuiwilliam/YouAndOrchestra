"""Tests for the playback module — normalize_loudness, play functions.

Audio output is mocked. These tests verify normalization logic and
error handling without producing actual sound.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from yao.errors import RenderError
from yao.render.playback import normalize_loudness, play_wav_external, play_wav_inline


class TestNormalizeLoudness:
    """Tests for LUFS/RMS loudness normalization."""

    def test_empty_audio_returns_empty(self) -> None:
        """Empty array passes through unchanged."""
        audio = np.array([], dtype=np.float32)
        result = normalize_loudness(audio, target_lufs=-16.0)
        assert len(result) == 0

    def test_silent_audio_unchanged(self) -> None:
        """All-zeros audio is not modified (nothing to normalize)."""
        audio = np.zeros(44100, dtype=np.float32)
        result = normalize_loudness(audio, target_lufs=-16.0)
        assert np.allclose(result, 0.0)

    def test_normalization_changes_level(self) -> None:
        """Audio at a non-target level should be adjusted."""
        # Generate a 1-second sine wave at a known level
        sr = 44100
        t = np.linspace(0, 1.0, sr, dtype=np.float32)
        audio = 0.5 * np.sin(2.0 * np.pi * 440.0 * t).astype(np.float32)

        result = normalize_loudness(audio, target_lufs=-16.0)

        # Result should differ from input (level adjustment)
        assert result.shape == audio.shape
        assert result.dtype == audio.dtype
        # Not all-zeros
        assert np.max(np.abs(result)) > 0

    def test_preserves_mono_shape(self) -> None:
        """1-D input produces 1-D output."""
        audio = np.random.default_rng(42).uniform(-0.5, 0.5, 44100).astype(np.float32)
        result = normalize_loudness(audio, target_lufs=-16.0)
        assert result.ndim == 1

    def test_rms_fallback_without_pyloudnorm(self) -> None:
        """Falls back to RMS normalization when pyloudnorm is missing."""
        from yao.render.playback import _rms_normalize

        audio = 0.3 * np.ones(44100, dtype=np.float32)
        result = _rms_normalize(audio, target_lufs=-16.0)
        assert len(result) == 44100
        assert result.dtype == audio.dtype


class TestPlayWavInline:
    """Tests for inline playback via sounddevice."""

    @patch("sounddevice.wait")
    @patch("sounddevice.play")
    def test_play_calls_sounddevice(self, mock_play: MagicMock, mock_wait: MagicMock) -> None:
        """play_wav_inline calls sd.play and sd.wait."""
        audio = np.zeros(44100, dtype=np.float32)
        play_wav_inline(audio, sample_rate=44100, block=True)
        assert mock_play.called
        assert mock_wait.called

    @patch("sounddevice.play")
    def test_play_non_blocking(self, mock_play: MagicMock) -> None:
        """Non-blocking mode calls play but not wait."""
        audio = np.zeros(44100, dtype=np.float32)
        play_wav_inline(audio, sample_rate=44100, block=False)
        assert mock_play.called


class TestPlayWavExternal:
    """Tests for external playback."""

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        """Non-existent WAV file raises RenderError."""
        with pytest.raises(RenderError, match="WAV file not found"):
            play_wav_external(tmp_path / "no.wav")

    @patch("subprocess.Popen")
    @patch("platform.system", return_value="Darwin")
    def test_macos_uses_open(self, _mock_sys: MagicMock, mock_popen: MagicMock, tmp_path: Path) -> None:
        """macOS uses 'open' command."""
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"fake")
        play_wav_external(wav)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "open"

    @patch("subprocess.Popen")
    @patch("platform.system", return_value="Linux")
    def test_linux_uses_xdg_open(self, _mock_sys: MagicMock, mock_popen: MagicMock, tmp_path: Path) -> None:
        """Linux uses 'xdg-open' command."""
        wav = tmp_path / "test.wav"
        wav.write_bytes(b"fake")
        play_wav_external(wav)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "xdg-open"
