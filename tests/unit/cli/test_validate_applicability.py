"""Tests for yao validate applicability report."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from cli.main import cli

V1_SPEC = """\
title: "Applicability Test"
key: "C major"
tempo_bpm: 120
time_signature: "4/4"
instruments:
  - name: piano
    role: melody
sections:
  - name: verse
    bars: 8
    dynamics: mf
"""

V2_SPEC_WITH_IGNORED = """\
version: "2"

identity:
  title: "Ignored Fields Test"
  duration_sec: 16

global:
  key: "C major"
  bpm: 120
  time_signature: "4/4"

emotion:
  valence: 0.5
  warmth: 0.8
  nostalgia: 0.7

form:
  sections:
    - id: verse
      bars: 8

arrangement:
  instruments:
    piano:
      role: melody

generation:
  strategy: rule_based
"""


class TestValidateApplicability:
    """Test that yao validate shows applicability report."""

    def test_v1_spec_shows_applied(self, tmp_path: Path) -> None:
        """V1 spec shows Applied fields."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(V1_SPEC)
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(spec_path)])
        assert result.exit_code == 0
        assert "Applied:" in result.output

    def test_v2_spec_shows_ignored(self, tmp_path: Path) -> None:
        """V2 spec with ignored fields shows Not yet honored section."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(V2_SPEC_WITH_IGNORED)
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(spec_path)])
        assert result.exit_code == 0
        assert "Not yet honored" in result.output
        assert "emotion.warmth" in result.output

    def test_v2_spec_shows_partial(self, tmp_path: Path) -> None:
        """V2 spec shows Partially applied section."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(V2_SPEC_WITH_IGNORED)
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", str(spec_path)])
        assert result.exit_code == 0
        assert "Partially applied:" in result.output

    def test_no_applicability_flag(self, tmp_path: Path) -> None:
        """--no-applicability suppresses the report."""
        spec_path = tmp_path / "test.yaml"
        spec_path.write_text(V1_SPEC)
        runner = CliRunner()
        result = runner.invoke(cli, ["validate", "--no-applicability", str(spec_path)])
        assert result.exit_code == 0
        assert "Field Applicability" not in result.output
