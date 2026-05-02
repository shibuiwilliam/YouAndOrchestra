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


@dataclass(frozen=True)
class GenerationParams:
    """Per-bar generation parameters derived from trajectory.

    Used by generators to dynamically adjust output across the timeline.
    Each field is derived from one or more trajectory dimensions.
    """

    velocity_modifier: int
    """Added to base velocity. Range ±20. From tension."""

    leap_probability: float
    """Probability of a melodic leap vs stepwise motion [0,1]. From tension."""

    note_density_factor: float
    """Multiplier on base note count [0.5, 2.0]. From density."""

    rhythmic_subdivision: int
    """Rhythmic grid: 4=quarter, 8=eighth, 16=sixteenth. From density."""

    register_offset: int
    """Semitone offset for melody register [-12, +12]. From register_height."""

    chord_extension_prob: float
    """Probability of adding 7th/9th to chords [0,1]. From tension."""

    motif_variation_rate: float
    """How much motifs vary on repetition [0,1]. From predictability (inverted)."""


_DEFAULT_PARAMS = GenerationParams(
    velocity_modifier=0,
    leap_probability=0.15,
    note_density_factor=1.0,
    rhythmic_subdivision=8,
    register_offset=0,
    chord_extension_prob=0.1,
    motif_variation_rate=0.3,
)


def derive_generation_params(
    trajectory: MultiDimensionalTrajectory,
    bar: int,
) -> GenerationParams:
    """Compute generation parameters for a specific bar from trajectory.

    Maps each trajectory dimension to relevant generation parameters.
    All mappings have musical rationale:

    - tension → velocity, leap probability, chord extensions
    - density → note count, rhythmic subdivision
    - register_height → octave/register offset
    - predictability → motif variation (inverted: low predict = more variation)
    - brightness → (reserved for future instrument/voicing selection)

    Args:
        trajectory: The multi-dimensional trajectory.
        bar: Bar number.

    Returns:
        GenerationParams for this bar.
    """
    tension = trajectory.value_at("tension", float(bar))
    density = trajectory.value_at("density", float(bar))
    predict = trajectory.value_at("predictability", float(bar))
    register = trajectory.value_at("register_height", float(bar))

    return GenerationParams(
        velocity_modifier=int((tension - 0.5) * 40),
        leap_probability=min(0.15 + tension * 0.4, 0.9),
        note_density_factor=0.5 + density * 1.5,
        rhythmic_subdivision=16 if density > 0.65 else 8,  # noqa: PLR2004
        register_offset=round((register - 0.5) * 24),
        chord_extension_prob=tension * 0.6,
        motif_variation_rate=1.0 - predict,
    )


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
