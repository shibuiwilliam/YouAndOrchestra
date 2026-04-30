"""Spec file loading utilities.

Provides high-level functions to load project specifications from disk.
Supports both v1 and v2 composition specs (auto-detected by ``version`` field).
Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from yao.errors import SpecValidationError
from yao.schema.composition import CompositionSpec
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.trajectory import TrajectorySpec


def load_composition_spec(path: Path) -> CompositionSpec:
    """Load a v1 composition spec from a YAML file.

    Args:
        path: Path to composition.yaml.

    Returns:
        Validated CompositionSpec.

    Raises:
        SpecValidationError: If loading or validation fails.
    """
    return CompositionSpec.from_yaml(path)


def load_composition_spec_v2(path: Path) -> CompositionSpecV2:
    """Load a v2 composition spec from a YAML file.

    Args:
        path: Path to composition.yaml (v2 format).

    Returns:
        Validated CompositionSpecV2.

    Raises:
        SpecValidationError: If loading or validation fails.
    """
    return CompositionSpecV2.from_yaml(path)


def load_composition_spec_auto(path: Path) -> CompositionSpec | CompositionSpecV2:
    """Load a composition spec, auto-detecting v1 vs v2 by the version field.

    Args:
        path: Path to composition.yaml.

    Returns:
        Either CompositionSpec (v1) or CompositionSpecV2.

    Raises:
        SpecValidationError: If loading or validation fails.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        raise SpecValidationError(f"Failed to load YAML: {e}") from e
    if not isinstance(data, dict):
        raise SpecValidationError("YAML root must be a mapping")

    if data.get("version") == "2":
        return CompositionSpecV2.from_yaml(path)
    return CompositionSpec.from_yaml(path)


def load_trajectory_spec(path: Path) -> TrajectorySpec:
    """Load a trajectory spec from a YAML file.

    Args:
        path: Path to trajectory.yaml.

    Returns:
        Validated TrajectorySpec.

    Raises:
        SpecValidationError: If loading or validation fails.
    """
    return TrajectorySpec.from_yaml(path)


def load_project_specs(
    project_dir: Path,
) -> tuple[CompositionSpec, TrajectorySpec | None]:
    """Load all specs for a project directory.

    Expects at minimum a ``composition.yaml``. Trajectory is optional.

    Args:
        project_dir: Path to the project directory under specs/projects/.

    Returns:
        Tuple of (CompositionSpec, optional TrajectorySpec).

    Raises:
        SpecValidationError: If required files are missing or invalid.
    """
    comp_path = project_dir / "composition.yaml"
    if not comp_path.exists():
        raise SpecValidationError(
            f"composition.yaml not found in {project_dir}",
            field="project_dir",
        )

    comp = load_composition_spec(comp_path)

    traj_path = project_dir / "trajectory.yaml"
    traj = load_trajectory_spec(traj_path) if traj_path.exists() else None

    return comp, traj
