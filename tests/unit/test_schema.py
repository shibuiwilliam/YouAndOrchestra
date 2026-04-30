"""Tests for specification schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from yao.errors import SpecValidationError
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec, Waypoint


class TestCompositionSpec:
    def test_valid_minimal_spec(self, minimal_spec: CompositionSpec) -> None:
        assert minimal_spec.title == "Test Composition"
        assert minimal_spec.key == "C major"
        assert minimal_spec.tempo_bpm == 120.0
        assert len(minimal_spec.instruments) == 1
        assert len(minimal_spec.sections) == 1

    def test_from_yaml_file(self, tmp_path: Path) -> None:
        data = {
            "title": "YAML Test",
            "key": "G major",
            "tempo_bpm": 100,
            "time_signature": "4/4",
            "total_bars": 8,
            "instruments": [{"name": "piano", "role": "melody"}],
            "sections": [{"name": "verse", "bars": 8, "dynamics": "mf"}],
        }
        yaml_path = tmp_path / "test.yaml"
        yaml_path.write_text(yaml.dump(data))

        spec = CompositionSpec.from_yaml(yaml_path)
        assert spec.title == "YAML Test"
        assert spec.key == "G major"

    def test_rejects_empty_title(self) -> None:
        with pytest.raises(SpecValidationError):
            CompositionSpec(
                title="",
                instruments=[InstrumentSpec(name="piano", role="melody")],
                sections=[SectionSpec(name="v", bars=8)],
            )

    def test_rejects_invalid_key(self) -> None:
        with pytest.raises(SpecValidationError):
            CompositionSpec(
                title="Test",
                key="X invalid",
                instruments=[InstrumentSpec(name="piano", role="melody")],
                sections=[SectionSpec(name="v", bars=8)],
            )

    def test_rejects_out_of_range_tempo(self) -> None:
        with pytest.raises(SpecValidationError):
            CompositionSpec(
                title="Test",
                tempo_bpm=999.0,
                instruments=[InstrumentSpec(name="piano", role="melody")],
                sections=[SectionSpec(name="v", bars=8)],
            )

    def test_rejects_negative_bars(self) -> None:
        with pytest.raises(SpecValidationError):
            SectionSpec(name="verse", bars=-1)

    def test_rejects_empty_instruments(self) -> None:
        with pytest.raises(SpecValidationError):
            CompositionSpec(
                title="Test",
                instruments=[],
                sections=[SectionSpec(name="v", bars=8)],
            )

    def test_rejects_empty_sections(self) -> None:
        with pytest.raises(SpecValidationError):
            CompositionSpec(
                title="Test",
                instruments=[InstrumentSpec(name="piano", role="melody")],
                sections=[],
            )

    def test_computed_total_bars(self) -> None:
        spec = CompositionSpec(
            title="Test",
            total_bars=0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="intro", bars=4),
                SectionSpec(name="verse", bars=8),
            ],
        )
        assert spec.computed_total_bars() == 12

    def test_computed_total_bars_explicit(self) -> None:
        spec = CompositionSpec(
            title="Test",
            total_bars=20,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=8)],
        )
        assert spec.computed_total_bars() == 20

    def test_rejects_invalid_dynamics(self) -> None:
        with pytest.raises(SpecValidationError):
            SectionSpec(name="verse", bars=8, dynamics="invalid")

    def test_from_template_file(self, spec_template_dir: Path) -> None:
        minimal = spec_template_dir / "minimal.yaml"
        if minimal.exists():
            spec = CompositionSpec.from_yaml(minimal)
            assert spec.title == "Minimal Example"


class TestTrajectorySpec:
    def test_linear_interpolation(self) -> None:
        from yao.schema.trajectory import TrajectoryDimension

        dim = TrajectoryDimension(
            type="linear",
            waypoints=[
                Waypoint(bar=0, value=0.0),
                Waypoint(bar=10, value=1.0),
            ],
        )
        assert dim.value_at(0) == 0.0
        assert dim.value_at(10) == 1.0
        assert abs(dim.value_at(5) - 0.5) < 0.01

    def test_value_before_first_waypoint(self) -> None:
        from yao.schema.trajectory import TrajectoryDimension

        dim = TrajectoryDimension(waypoints=[Waypoint(bar=5, value=0.3), Waypoint(bar=10, value=0.8)])
        assert dim.value_at(0) == 0.3

    def test_value_after_last_waypoint(self) -> None:
        from yao.schema.trajectory import TrajectoryDimension

        dim = TrajectoryDimension(waypoints=[Waypoint(bar=0, value=0.2), Waypoint(bar=10, value=0.8)])
        assert dim.value_at(20) == 0.8

    def test_target_value(self) -> None:
        from yao.schema.trajectory import TrajectoryDimension

        dim = TrajectoryDimension(target=0.65)
        assert dim.value_at(0) == 0.65
        assert dim.value_at(100) == 0.65

    def test_trajectory_spec_value_at(self) -> None:
        from yao.schema.trajectory import TrajectoryDimension

        spec = TrajectorySpec(
            tension=TrajectoryDimension(waypoints=[Waypoint(bar=0, value=0.2), Waypoint(bar=10, value=0.8)])
        )
        assert abs(spec.value_at("tension", 5) - 0.5) < 0.01
        assert spec.value_at("density", 5) == 0.5  # undefined dimension

    def test_from_yaml(self, tmp_path: Path) -> None:
        data = {
            "trajectories": {
                "tension": {
                    "type": "linear",
                    "waypoints": [[0, 0.2], [10, 0.8]],
                }
            }
        }
        yaml_path = tmp_path / "traj.yaml"
        yaml_path.write_text(yaml.dump(data))

        spec = TrajectorySpec.from_yaml(yaml_path)
        assert spec.tension is not None
        assert abs(spec.value_at("tension", 5) - 0.5) < 0.01
