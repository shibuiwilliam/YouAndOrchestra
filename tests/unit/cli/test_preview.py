"""Tests for yao preview command.

Audio playback is mocked — these tests verify generation and synthesis
pipeline, not actual sound output (environment-dependent).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from click.testing import CliRunner

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from cli.main import preview

MINIMAL_SPEC = """\
title: "Preview Test"
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


class TestPreviewCommand:
    """Test yao preview with mocked audio."""

    @patch("yao.render.midi_writer.score_ir_to_midi")
    @patch("sounddevice.play")
    @patch("sounddevice.wait")
    def test_preview_generates_and_plays(
        self,
        mock_wait: MagicMock,
        mock_play: MagicMock,
        mock_to_midi: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Preview must load spec, generate, synthesize, and play."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(MINIMAL_SPEC)

        # Mock the MIDI → audio pipeline
        mock_midi = MagicMock()
        mock_midi.fluidsynth.return_value = np.zeros(44100, dtype=np.float32)
        mock_to_midi.return_value = mock_midi

        # Create a fake soundfont so _find_soundfont works
        sf_dir = tmp_path / "soundfonts"
        sf_dir.mkdir()
        sf_file = sf_dir / "test.sf2"
        sf_file.write_bytes(b"fake")

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create soundfonts dir in working directory
            Path("soundfonts").mkdir()
            (Path("soundfonts") / "test.sf2").write_bytes(b"fake")

            result = runner.invoke(preview, [str(spec_path), "--seed", "42"])

        assert result.exit_code == 0, result.output
        assert mock_to_midi.called, "Should convert ScoreIR to PrettyMIDI"
        assert mock_play.called, "Should call sounddevice.play"

    def test_preview_missing_spec_fails(self, tmp_path: Path) -> None:
        """Preview with nonexistent spec should fail."""
        runner = CliRunner()
        result = runner.invoke(preview, [str(tmp_path / "nonexistent.yaml")])
        assert result.exit_code != 0
