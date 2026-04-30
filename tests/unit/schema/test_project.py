"""Tests for CompositionProject loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yao.errors import SpecValidationError
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.project import CompositionProject


def _write_minimal_v2(project_dir: Path) -> None:
    """Write a minimal v2 project to a directory."""
    comp = {
        "version": "2",
        "identity": {"title": "Test", "duration_sec": 32},
        "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
        "form": {"sections": [{"id": "intro", "bars": 8}, {"id": "main", "bars": 8}]},
        "arrangement": {"instruments": {"piano": {"role": "melody"}}},
    }
    (project_dir / "composition.yaml").write_text(yaml.dump(comp, default_flow_style=False))


def _write_v1_spec(project_dir: Path) -> None:
    """Write a v1 spec to a directory."""
    comp = {
        "title": "V1 Test",
        "key": "C major",
        "tempo_bpm": 120,
        "time_signature": "4/4",
        "instruments": [{"name": "piano", "role": "melody"}],
        "sections": [{"name": "intro", "bars": 8}],
    }
    (project_dir / "composition.yaml").write_text(yaml.dump(comp, default_flow_style=False))


class TestProjectLoad:
    """CompositionProject.load() tests."""

    def test_load_v2_project(self, tmp_path: Path) -> None:
        _write_minimal_v2(tmp_path)
        (tmp_path / "intent.md").write_text("# Test\n\nA calm ambient piece for studying.")
        project = CompositionProject.load(tmp_path)
        assert isinstance(project.spec, CompositionSpecV2)
        assert project.title == "Test"
        assert "calm" in project.intent.keywords
        assert project.trajectory.tension.value_at(0) == 0.5  # default

    def test_load_v1_project(self, tmp_path: Path) -> None:
        _write_v1_spec(tmp_path)
        project = CompositionProject.load(tmp_path)
        assert project.title == "V1 Test"

    def test_load_with_trajectory(self, tmp_path: Path) -> None:
        _write_minimal_v2(tmp_path)
        traj = {
            "trajectories": {
                "tension": {
                    "type": "bezier",
                    "waypoints": [[0, 0.2], [16, 0.9]],
                },
            }
        }
        (tmp_path / "trajectory.yaml").write_text(yaml.dump(traj, default_flow_style=False))
        project = CompositionProject.load(tmp_path)
        assert project.trajectory.tension.value_at(0) == 0.2
        assert project.trajectory.tension.value_at(16) == 0.9

    def test_load_without_intent(self, tmp_path: Path) -> None:
        _write_minimal_v2(tmp_path)
        project = CompositionProject.load(tmp_path)
        assert project.intent.text == ""
        assert not project.intent.crystallized()

    def test_load_missing_composition_fails(self, tmp_path: Path) -> None:
        with pytest.raises(SpecValidationError, match="composition.yaml not found"):
            CompositionProject.load(tmp_path)


class TestFromSpecFile:
    """CompositionProject.from_spec_file() tests."""

    def test_from_spec_file(self, tmp_path: Path) -> None:
        _write_minimal_v2(tmp_path)
        project = CompositionProject.from_spec_file(tmp_path / "composition.yaml")
        assert project.title == "Test"
        assert project.intent.text == ""
        assert project.trajectory.tension.value_at(0) == 0.5
