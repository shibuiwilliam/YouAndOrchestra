"""Tests for multi-dimensional trajectory IR."""

from __future__ import annotations

import pytest

from yao.ir.trajectory import MultiDimensionalTrajectory, TrajectoryCurve
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec, Waypoint


class TestTrajectoryCurve:
    """TrajectoryCurve value_at tests."""

    def test_linear_target(self) -> None:
        curve = TrajectoryCurve(curve_type="linear", target=0.7)
        assert curve.value_at(0) == 0.7
        assert curve.value_at(100) == 0.7

    def test_waypoint_interpolation(self) -> None:
        curve = TrajectoryCurve(
            curve_type="bezier",
            waypoints=((0.0, 0.0), (10.0, 1.0)),
        )
        assert curve.value_at(0) == 0.0
        assert curve.value_at(10) == 1.0
        assert curve.value_at(5) == pytest.approx(0.5)

    def test_waypoint_clamp_before(self) -> None:
        curve = TrajectoryCurve(
            curve_type="bezier",
            waypoints=((4.0, 0.3), (8.0, 0.9)),
        )
        assert curve.value_at(0) == 0.3

    def test_waypoint_clamp_after(self) -> None:
        curve = TrajectoryCurve(
            curve_type="bezier",
            waypoints=((0.0, 0.2), (10.0, 0.8)),
        )
        assert curve.value_at(100) == 0.8

    def test_stepped_with_section(self) -> None:
        curve = TrajectoryCurve(
            curve_type="stepped",
            sections={"intro": 0.2, "chorus": 0.9},
        )
        assert curve.value_at(0, section_name="intro") == 0.2
        assert curve.value_at(0, section_name="chorus") == 0.9
        assert curve.value_at(0, section_name="unknown") == 0.5

    def test_empty_curve_default(self) -> None:
        curve = TrajectoryCurve(curve_type="bezier")
        assert curve.value_at(5) == 0.5

    def test_multi_waypoint(self) -> None:
        curve = TrajectoryCurve(
            curve_type="bezier",
            waypoints=((0.0, 0.1), (10.0, 0.5), (20.0, 0.9)),
        )
        assert curve.value_at(0) == 0.1
        assert curve.value_at(5) == pytest.approx(0.3)
        assert curve.value_at(10) == 0.5
        assert curve.value_at(15) == pytest.approx(0.7)
        assert curve.value_at(20) == 0.9


class TestMultiDimensionalTrajectory:
    """MultiDimensionalTrajectory tests."""

    def test_uniform(self) -> None:
        traj = MultiDimensionalTrajectory.uniform(0.3)
        assert traj.tension.value_at(0) == 0.3
        assert traj.brightness.value_at(100) == 0.3
        assert traj.register_height.value_at(50) == 0.3

    def test_default(self) -> None:
        traj = MultiDimensionalTrajectory.default()
        for dim in traj.all_dimensions().values():
            assert dim.value_at(0) == 0.5

    def test_all_dimensions_count(self) -> None:
        traj = MultiDimensionalTrajectory.default()
        assert len(traj.all_dimensions()) == 5

    def test_value_at_named(self) -> None:
        traj = MultiDimensionalTrajectory(
            tension=TrajectoryCurve(curve_type="linear", target=0.9),
            density=TrajectoryCurve(curve_type="linear", target=0.1),
            predictability=TrajectoryCurve(curve_type="linear", target=0.5),
            brightness=TrajectoryCurve(curve_type="linear", target=0.7),
            register_height=TrajectoryCurve(curve_type="linear", target=0.3),
        )
        assert traj.value_at("tension", 0) == 0.9
        assert traj.value_at("density", 0) == 0.1
        assert traj.value_at("brightness", 0) == 0.7
        assert traj.value_at("register_height", 0) == 0.3

    def test_value_at_unknown_dimension(self) -> None:
        traj = MultiDimensionalTrajectory.default()
        assert traj.value_at("nonexistent", 0) == 0.5


class TestFromSpec:
    """MultiDimensionalTrajectory.from_spec conversion."""

    def test_from_v1_spec(self) -> None:
        spec = TrajectorySpec(
            tension=TrajectoryDimension(
                type="bezier",
                waypoints=[Waypoint(bar=0, value=0.2), Waypoint(bar=16, value=0.8)],
            ),
            density=TrajectoryDimension(type="linear", target=0.6),
        )
        traj = MultiDimensionalTrajectory.from_spec(spec)
        assert traj.tension.value_at(0) == 0.2
        assert traj.tension.value_at(16) == 0.8
        assert traj.density.value_at(0) == 0.6
        # Unset dimensions default to 0.5
        assert traj.brightness.value_at(0) == 0.5
        assert traj.register_height.value_at(0) == 0.5

    def test_from_v2_spec_with_brightness(self) -> None:
        spec = TrajectorySpec(
            tension=TrajectoryDimension(type="linear", target=0.5),
            density=TrajectoryDimension(type="linear", target=0.5),
            predictability=TrajectoryDimension(type="linear", target=0.5),
            brightness=TrajectoryDimension(type="linear", target=0.8),
            register_height=TrajectoryDimension(type="linear", target=0.3),
        )
        traj = MultiDimensionalTrajectory.from_spec(spec)
        assert traj.brightness.value_at(0) == 0.8
        assert traj.register_height.value_at(0) == 0.3

    def test_from_none_returns_default(self) -> None:
        traj = MultiDimensionalTrajectory.from_spec(None)
        assert traj.tension.value_at(0) == 0.5


class TestTrajectorySpecV2Dimensions:
    """TrajectorySpec now supports 5 dimensions."""

    def test_brightness_field(self) -> None:
        spec = TrajectorySpec(
            brightness=TrajectoryDimension(type="linear", target=0.9),
        )
        assert spec.value_at("brightness", 0) == 0.9

    def test_register_height_field(self) -> None:
        spec = TrajectorySpec(
            register_height=TrajectoryDimension(
                type="bezier",
                waypoints=[Waypoint(bar=0, value=0.3), Waypoint(bar=16, value=0.7)],
            ),
        )
        assert spec.value_at("register_height", 8) == pytest.approx(0.5)
