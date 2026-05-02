"""Tests for yao watch command.

Audio playback and file watching are mocked. These tests verify the
watch handler logic without requiring a real filesystem observer.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from cli.main import watch

# sounddevice requires PortAudio — skip tests on CI without it
_sd = pytest.importorskip("sounddevice", reason="PortAudio not available")

MINIMAL_SPEC = """\
title: "Watch Test"
key: "C major"
tempo_bpm: 120
time_signature: "4/4"
instruments:
  - name: piano
    role: melody
sections:
  - name: verse
    bars: 4
    dynamics: mf
generation:
  strategy: rule_based
  seed: 42
"""


class TestWatchCommand:
    """Test yao watch with mocked dependencies."""

    def test_watch_missing_spec_fails(self, tmp_path: Path) -> None:
        """Watch with nonexistent spec should fail."""
        runner = CliRunner()
        result = runner.invoke(watch, [str(tmp_path / "nonexistent.yaml")])
        assert result.exit_code != 0

    @patch("yao.render.midi_writer.score_ir_to_midi")
    @patch("sounddevice.play")
    @patch("sounddevice.stop")
    @patch("watchdog.observers.Observer")
    def test_watch_starts_observer_and_plays(
        self,
        mock_observer_cls: MagicMock,
        mock_sd_stop: MagicMock,
        mock_sd_play: MagicMock,
        mock_to_midi: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Watch must start observer and play initial audio."""
        import numpy as np

        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(MINIMAL_SPEC)

        mock_midi = MagicMock()
        mock_midi.fluidsynth.return_value = np.zeros(44100, dtype=np.float32)
        mock_to_midi.return_value = mock_midi

        # Mock observer to not actually watch
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer

        runner = CliRunner()
        # The watch command runs forever — we simulate KeyboardInterrupt
        # by making time.sleep raise it immediately
        with (
            runner.isolated_filesystem(temp_dir=tmp_path),
            patch("time.sleep", side_effect=KeyboardInterrupt),
        ):
            Path("soundfonts").mkdir()
            (Path("soundfonts") / "test.sf2").write_bytes(b"fake")

            runner.invoke(watch, [str(spec_path)])

        # Should have started the observer
        assert mock_observer.start.called
        # Should have played initial audio
        assert mock_sd_play.called
        # Should have stopped cleanly
        assert mock_observer.stop.called
