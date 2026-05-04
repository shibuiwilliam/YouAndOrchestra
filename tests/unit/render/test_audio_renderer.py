"""Tests for audio renderer — AudioRenderResult and FluidSynth integration.

FluidSynth availability is not guaranteed in CI, so subprocess calls
are mocked. The tests verify the render function's logic, error handling,
and AudioRenderResult structure.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yao.errors import RenderError
from yao.render.audio_renderer import AudioRenderResult, render_midi_to_wav


class TestAudioRenderResult:
    """Tests for the AudioRenderResult dataclass."""

    def test_fields(self) -> None:
        """AudioRenderResult has all required fields."""
        result = AudioRenderResult(
            output_path=Path("/tmp/test.wav"),
            sample_rate=44100,
            duration_seconds=2.5,
            channels=2,
        )
        assert result.output_path == Path("/tmp/test.wav")
        assert result.sample_rate == 44100
        assert result.duration_seconds == 2.5
        assert result.channels == 2

    def test_frozen(self) -> None:
        """AudioRenderResult is immutable."""
        result = AudioRenderResult(
            output_path=Path("/tmp/test.wav"),
            sample_rate=44100,
            duration_seconds=1.0,
            channels=1,
        )
        with pytest.raises(AttributeError):
            result.sample_rate = 48000  # type: ignore[misc]


class TestRenderMidiToWav:
    """Tests for render_midi_to_wav with mocked fluidsynth."""

    def test_missing_midi_raises(self, tmp_path: Path) -> None:
        """Non-existent MIDI file raises RenderError."""
        with pytest.raises(RenderError, match="MIDI file not found"):
            render_midi_to_wav(tmp_path / "no.mid", tmp_path / "out.wav")

    @patch("shutil.which", return_value=None)
    def test_missing_fluidsynth_raises(self, _mock_which: MagicMock, tmp_path: Path) -> None:
        """Missing fluidsynth gives clear install instructions."""
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"fake")

        with pytest.raises(RenderError, match="fluidsynth is not installed"):
            render_midi_to_wav(midi_file, tmp_path / "out.wav")

    @patch("shutil.which", return_value=None)
    def test_error_message_has_install_instructions(self, _mock_which: MagicMock, tmp_path: Path) -> None:
        """Error message includes brew and apt-get instructions."""
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"fake")

        with pytest.raises(RenderError, match="brew install") as exc_info:
            render_midi_to_wav(midi_file, tmp_path / "out.wav")
        assert "apt-get" in str(exc_info.value)

    def test_missing_soundfont_raises(self, tmp_path: Path) -> None:
        """Missing SoundFont raises RenderError with instructions."""
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"fake")

        with (
            patch("shutil.which", return_value="/usr/bin/fluidsynth"),
            pytest.raises(RenderError, match="No SoundFont found"),
        ):
            render_midi_to_wav(midi_file, tmp_path / "out.wav")

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/fluidsynth")
    def test_successful_render_returns_result(
        self,
        _mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Successful render returns AudioRenderResult with WAV metadata."""
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"fake")
        sf_file = tmp_path / "test.sf2"
        sf_file.write_bytes(b"fake")
        wav_out = tmp_path / "out.wav"

        # Create a valid WAV file as the mock output
        def _create_wav(*_args: object, **_kwargs: object) -> MagicMock:
            _write_test_wav(wav_out, sample_rate=44100, channels=2, n_frames=44100)
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        mock_run.side_effect = _create_wav

        result = render_midi_to_wav(midi_file, wav_out, sf_file)

        assert isinstance(result, AudioRenderResult)
        assert result.output_path == wav_out
        assert result.sample_rate == 44100
        assert result.channels == 2
        assert result.duration_seconds == pytest.approx(1.0, abs=0.01)

    @patch("subprocess.run")
    @patch("shutil.which", return_value="/usr/bin/fluidsynth")
    def test_render_failure_raises(
        self,
        _mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Non-zero exit code from fluidsynth raises RenderError."""
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"fake")
        sf_file = tmp_path / "test.sf2"
        sf_file.write_bytes(b"fake")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some error"
        mock_run.return_value = mock_result

        with pytest.raises(RenderError, match="exited with code 1"):
            render_midi_to_wav(midi_file, tmp_path / "out.wav", sf_file)


def _write_test_wav(path: Path, *, sample_rate: int, channels: int, n_frames: int) -> None:
    """Write a minimal valid WAV file for testing."""
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        # Write silence
        wf.writeframes(struct.pack(f"<{n_frames * channels}h", *([0] * n_frames * channels)))
