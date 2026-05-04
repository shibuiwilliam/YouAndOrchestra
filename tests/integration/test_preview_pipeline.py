"""Integration test: preview pipeline end-to-end timing.

Verifies that the spec → generate → synthesize pipeline completes
within the performance budget. Audio playback is mocked.
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from click.testing import CliRunner

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401

# sounddevice requires PortAudio — skip on CI without it
try:
    import sounddevice as _sd  # noqa: F401
except OSError:
    pytest.skip("PortAudio not available", allow_module_level=True)

from cli.main import preview

MINIMAL_SPEC = """\
title: "Timing Test"
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


@pytest.mark.integration
class TestPreviewPipeline:
    """End-to-end preview timing and --save flag tests."""

    @patch("yao.render.midi_writer.score_ir_to_midi")
    @patch("sounddevice.play")
    @patch("sounddevice.wait")
    def test_preview_completes_within_budget(
        self,
        mock_wait: MagicMock,
        mock_play: MagicMock,
        mock_to_midi: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Preview pipeline (without audio rendering) completes in <3s."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(MINIMAL_SPEC)

        mock_midi = MagicMock()
        mock_midi.fluidsynth.return_value = np.zeros(44100, dtype=np.float32)
        mock_to_midi.return_value = mock_midi

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("soundfonts").mkdir()
            (Path("soundfonts") / "test.sf2").write_bytes(b"fake")

            start = time.monotonic()
            result = runner.invoke(preview, [str(spec_path), "--seed", "42"])
            elapsed = time.monotonic() - start

        assert result.exit_code == 0, result.output
        assert elapsed < 3.0, f"Preview took {elapsed:.1f}s, budget is <3s"

    @patch("sounddevice.play")
    @patch("sounddevice.wait")
    def test_preview_save_flag_writes_artifacts(
        self,
        mock_wait: MagicMock,
        mock_play: MagicMock,
        tmp_path: Path,
    ) -> None:
        """--save flag writes MIDI and provenance alongside playback."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(MINIMAL_SPEC)
        save_dir = tmp_path / "saved"

        runner = CliRunner()
        sf_dir = tmp_path / "soundfonts"
        sf_dir.mkdir()
        (sf_dir / "test.sf2").write_bytes(b"fake")

        # Don't mock score_ir_to_midi — let real generation + MIDI write happen.
        # Mock fluidsynth call on the PrettyMIDI object to avoid needing a real SoundFont.
        with (
            patch("cli.main._find_soundfont", return_value=sf_dir / "test.sf2"),
            patch("pretty_midi.PrettyMIDI.fluidsynth", return_value=np.zeros(44100, dtype=np.float32)),
        ):
            result = runner.invoke(
                preview,
                [str(spec_path), "--seed", "42", "--save", str(save_dir)],
            )

        assert result.exit_code == 0, result.output
        assert (save_dir / "full.mid").exists(), "MIDI not saved"
        assert (save_dir / "provenance.json").exists(), "Provenance not saved"
