"""Multi-dimensional trajectory — Layer 3 IR representation.

A trajectory is a set of time-axis curves that generators use as
control signals. Each dimension maps a time point to a [0, 1] value.

This module provides the frozen dataclass ``MultiDimensionalTrajectory``
which is the canonical form consumed by generators and plan generators.
The schema-level ``TrajectorySpec`` (Layer 1) is converted to this form
via ``from_spec()``.

Belongs to Layer 3 (IR), alongside ScoreIR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TrajectoryCurve:
    """A single trajectory dimension as a time-axis curve.

    Attributes:
        curve_type: Interpolation method.
        waypoints: List of (time_position, value) pairs. Time is in bars.
        sections: Section name → flat value mapping (for stepped type).
        target: Fixed target value (for linear type).
        variance: Allowed deviation from target (for linear type).
    """

    curve_type: Literal["bezier", "stepped", "linear"]
    waypoints: tuple[tuple[float, float], ...] = ()
    sections: dict[str, float] | None = None
    target: float | None = None
    variance: float | None = None

    def value_at(self, bar: float, section_name: str | None = None) -> float:
        """Interpolate the curve value at a given bar.

        Args:
            bar: Bar number (float for sub-bar precision).
            section_name: Current section name (used for stepped type).

        Returns:
            Value in [0.0, 1.0].
        """
        if self.curve_type == "stepped" and self.sections and section_name:
            return self.sections.get(section_name, 0.5)

        if self.target is not None:
            return self.target

        if not self.waypoints:
            return 0.5

        # Clamp to endpoint values
        if bar <= self.waypoints[0][0]:
            return self.waypoints[0][1]
        if bar >= self.waypoints[-1][0]:
            return self.waypoints[-1][1]

        # Linear interpolation between waypoints
        for i in range(len(self.waypoints) - 1):
            t0, v0 = self.waypoints[i]
            t1, v1 = self.waypoints[i + 1]
            if t0 <= bar <= t1:
                if t1 == t0:
                    return v0
                frac = (bar - t0) / (t1 - t0)
                return v0 + frac * (v1 - v0)

        return 0.5


def _default_curve() -> TrajectoryCurve:
    """Create a flat 0.5 curve (neutral default)."""
    return TrajectoryCurve(curve_type="linear", target=0.5)


@dataclass(frozen=True)
class MultiDimensionalTrajectory:
    """Five-dimensional trajectory — the common control signal for all generators.

    Every generator must respond to changes in these dimensions.
    See CLAUDE.md Rule #7: "Trajectory is a control signal, not a decoration."

    Attributes:
        tension: Musical tension (0=relaxed, 1=tense).
        density: Note density (0=sparse, 1=dense).
        predictability: Predictability (0=surprising, 1=predictable).
        brightness: Timbral brightness (0=dark, 1=bright). New in v2.
        register_height: Register height (0=low, 1=high). New in v2.
    """

    tension: TrajectoryCurve
    density: TrajectoryCurve
    predictability: TrajectoryCurve
    brightness: TrajectoryCurve
    register_height: TrajectoryCurve

    def all_dimensions(self) -> dict[str, TrajectoryCurve]:
        """Return all dimensions as a name → curve mapping."""
        return {
            "tension": self.tension,
            "density": self.density,
            "predictability": self.predictability,
            "brightness": self.brightness,
            "register_height": self.register_height,
        }

    def value_at(self, dimension: str, bar: float, section_name: str | None = None) -> float:
        """Get the value of a dimension at a given bar.

        Args:
            dimension: Dimension name.
            bar: Bar number.
            section_name: Current section name (for stepped curves).

        Returns:
            Value in [0.0, 1.0], or 0.5 if dimension is unknown.
        """
        dims = self.all_dimensions()
        curve = dims.get(dimension)
        if curve is None:
            return 0.5
        return curve.value_at(bar, section_name)

    @classmethod
    def uniform(cls, value: float) -> MultiDimensionalTrajectory:
        """Create a trajectory where all dimensions are flat at the given value.

        Useful for testing and as a baseline.

        Args:
            value: Uniform value for all dimensions.

        Returns:
            MultiDimensionalTrajectory with all curves at the given value.
        """
        curve = TrajectoryCurve(curve_type="linear", target=value)
        return cls(
            tension=curve,
            density=curve,
            predictability=curve,
            brightness=curve,
            register_height=curve,
        )

    @classmethod
    def default(cls) -> MultiDimensionalTrajectory:
        """Create a neutral default trajectory (all dimensions at 0.5)."""
        return cls.uniform(0.5)

    @classmethod
    def from_spec(cls, spec: object) -> MultiDimensionalTrajectory:
        """Convert a TrajectorySpec (Layer 1 Pydantic model) to this IR form.

        Handles both the v1 TrajectorySpec (3 dimensions) and future v2
        trajectory specs (5 dimensions).

        Args:
            spec: A TrajectorySpec instance.

        Returns:
            MultiDimensionalTrajectory with all 5 dimensions.
        """
        # Import here to avoid circular dependency (Layer 3 should not
        # depend on Layer 1 at module level, but this factory is a
        # convenience bridge).
        from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec

        if not isinstance(spec, TrajectorySpec):
            return cls.default()

        def _convert_dim(dim: TrajectoryDimension | None) -> TrajectoryCurve:
            if dim is None:
                return _default_curve()
            waypoints = tuple((float(w.bar), w.value) for w in dim.waypoints)
            return TrajectoryCurve(
                curve_type=dim.type,
                waypoints=waypoints,
                sections=dim.sections if dim.sections else None,
                target=dim.target,
                variance=dim.variance,
            )

        return cls(
            tension=_convert_dim(spec.tension),
            density=_convert_dim(spec.density),
            predictability=_convert_dim(spec.predictability),
            brightness=_convert_dim(getattr(spec, "brightness", None)),
            register_height=_convert_dim(getattr(spec, "register_height", None)),
        )
