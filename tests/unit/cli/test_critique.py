"""Tests for yao critique CLI command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from click.testing import CliRunner

if TYPE_CHECKING:
    import pytest

from cli.main import cli


class TestCritiqueCommand:
    """Tests for yao critique."""

    def test_critique_help(self) -> None:
        """yao critique --help should display usage."""
        runner = CliRunner()
        result = runner.invoke(cli, ["critique", "--help"])
        assert result.exit_code == 0
        assert "adversarial critique" in result.output.lower()

    def test_critique_missing_project(self) -> None:
        """yao critique with nonexistent project should fail gracefully."""
        runner = CliRunner()
        result = runner.invoke(cli, ["critique", "nonexistent-project"])
        assert result.exit_code != 0

    def test_critique_runs_on_valid_project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """yao critique should produce findings for a valid project."""
        # Create project structure with a minimal spec
        project_dir = tmp_path / "specs" / "projects" / "test-song"
        project_dir.mkdir(parents=True)
        spec_content = """\
title: Test Song
key: C major
tempo_bpm: 120
time_signature: "4/4"
duration_bars: 8
genre: pop
instruments:
  - name: piano
    role: melody
sections:
  - name: verse
    bars: 8
    dynamics: mf
generation:
  strategy: rule_based
  seed: 42
"""
        (project_dir / "composition.yaml").write_text(spec_content)

        # Create output dir
        output_dir = tmp_path / "outputs" / "projects" / "test-song" / "iterations" / "v001"
        output_dir.mkdir(parents=True)

        # Monkeypatch working directory
        monkeypatch.chdir(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli, ["critique", "test-song"])

        assert result.exit_code == 0
        assert "Critique written to" in result.output
        assert "Total findings:" in result.output

        # Verify critique.md was written
        critique_file = output_dir / "critique.md"
        assert critique_file.exists()
        content = critique_file.read_text()
        assert "# Adversarial Critique" in content
