"""Pydantic models for trajectory.yaml specification.

Trajectories define the time-axis shape of a composition: tension, density,
predictability, and other dimensions as curves over bars. They belong to
Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError


class Waypoint(BaseModel):
    """A single point on a trajectory curve: [bar, value]."""

    bar: int
    value: float

    @field_validator("value")
    @classmethod
    def value_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Trajectory value must be in [0.0, 1.0], got {v}",
                field="value",
            )
        return v


class TrajectoryDimension(BaseModel):
    """A single trajectory dimension (e.g., tension, density)."""

    type: Literal["bezier", "stepped", "linear"] = "linear"
    waypoints: list[Waypoint] = []
    sections: dict[str, float] = {}
    target: float | None = None
    variance: float | None = None

    def value_at(self, bar: int) -> float:
        """Interpolate the trajectory value at a given bar.

        For stepped type, returns the section value.
        For bezier/linear, performs linear interpolation between waypoints.
        For target type, returns the target value.

        Args:
            bar: The bar number to query.

        Returns:
            Interpolated value in [0.0, 1.0].
        """
        if self.target is not None:
            return self.target

        if not self.waypoints:
            return 0.5

        if bar <= self.waypoints[0].bar:
            return self.waypoints[0].value
        if bar >= self.waypoints[-1].bar:
            return self.waypoints[-1].value

        for i in range(len(self.waypoints) - 1):
            w0 = self.waypoints[i]
            w1 = self.waypoints[i + 1]
            if w0.bar <= bar <= w1.bar:
                if w1.bar == w0.bar:
                    return w0.value
                t = (bar - w0.bar) / (w1.bar - w0.bar)
                return w0.value + t * (w1.value - w0.value)

        return 0.5


_ALL_DIMENSION_NAMES = ("tension", "density", "predictability", "brightness", "register_height")


class TrajectorySpec(BaseModel):
    """Complete trajectory specification for a composition.

    Contains one or more named trajectory dimensions. v1 supports tension,
    density, and predictability. v2 adds brightness and register_height.
    """

    tension: TrajectoryDimension | None = None
    density: TrajectoryDimension | None = None
    predictability: TrajectoryDimension | None = None
    brightness: TrajectoryDimension | None = None
    register_height: TrajectoryDimension | None = None

    def value_at(self, dimension: str, bar: int) -> float:
        """Get the trajectory value for a dimension at a given bar.

        Args:
            dimension: Name of the trajectory dimension.
            bar: Bar number.

        Returns:
            Value in [0.0, 1.0], or 0.5 if dimension is not defined.
        """
        dim: TrajectoryDimension | None = getattr(self, dimension, None)
        if dim is None:
            return 0.5
        return dim.value_at(bar)

    @classmethod
    def from_yaml(cls, path: Path) -> TrajectorySpec:
        """Load and validate a trajectory spec from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Validated TrajectorySpec.

        Raises:
            SpecValidationError: If the YAML is invalid.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load trajectory YAML: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("Trajectory YAML root must be a mapping")
        # Support nested "trajectories" key or flat format
        if "trajectories" in data:
            data = data["trajectories"]
        # Convert list waypoints [[bar, val], ...] to Waypoint objects
        for dim_name in _ALL_DIMENSION_NAMES:
            if dim_name in data and isinstance(data[dim_name], dict):
                dim_data = data[dim_name]
                if "waypoints" in dim_data and isinstance(dim_data["waypoints"], list):
                    converted = []
                    for wp in dim_data["waypoints"]:
                        if isinstance(wp, list) and len(wp) == 2:  # noqa: PLR2004
                            converted.append({"bar": wp[0], "value": wp[1]})
                        else:
                            converted.append(wp)
                    dim_data["waypoints"] = converted
        try:
            return cls.model_validate(data)
        except Exception as e:
            raise SpecValidationError(f"Trajectory validation failed: {e}") from e
