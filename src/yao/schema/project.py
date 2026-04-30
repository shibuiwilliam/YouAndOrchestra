"""CompositionProject — aggregates spec, intent, and trajectory.

A project directory contains multiple files (composition.yaml, intent.md,
trajectory.yaml, etc.). CompositionProject loads and validates them together,
providing a single entry point for the pipeline.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from yao.errors import SpecValidationError
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import CompositionSpec
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec
from yao.schema.loader import load_composition_spec_auto, load_trajectory_spec


@dataclass(frozen=True)
class CompositionProject:
    """Aggregated project: spec + intent + trajectory.

    Keeps separation of concerns: CompositionSpecV2 holds the musical spec,
    IntentSpec holds the human intent, MultiDimensionalTrajectory holds the
    time-axis control signals. This class is the bundle that the pipeline
    receives.

    Attributes:
        spec: The composition specification (v1 or v2).
        intent: The parsed intent (may be a minimal default if no intent.md).
        trajectory: Multi-dimensional trajectory (5 dimensions).
        project_dir: Path to the project directory (for resolving relative paths).
    """

    spec: CompositionSpec | CompositionSpecV2
    intent: IntentSpec
    trajectory: MultiDimensionalTrajectory
    project_dir: Path | None = None

    @classmethod
    def load(cls, project_dir: Path) -> CompositionProject:
        """Load a full project from a directory.

        Expects at minimum a ``composition.yaml``. Intent and trajectory
        are optional — defaults are used when absent.

        Args:
            project_dir: Path to the project directory.

        Returns:
            A fully loaded CompositionProject.

        Raises:
            SpecValidationError: If required files are missing or invalid.
        """
        comp_path = project_dir / "composition.yaml"
        if not comp_path.exists():
            raise SpecValidationError(
                f"composition.yaml not found in {project_dir}",
                field="project_dir",
            )

        spec = load_composition_spec_auto(comp_path)

        # Intent: optional, default to minimal
        intent_path = project_dir / "intent.md"
        if intent_path.exists():
            intent = IntentSpec.from_markdown(intent_path)
        else:
            intent = IntentSpec(text="", keywords=[])

        # Trajectory: optional, default to neutral
        traj_path = project_dir / "trajectory.yaml"
        if traj_path.exists():
            traj_spec = load_trajectory_spec(traj_path)
            trajectory = MultiDimensionalTrajectory.from_spec(traj_spec)
        else:
            trajectory = MultiDimensionalTrajectory.default()

        return cls(
            spec=spec,
            intent=intent,
            trajectory=trajectory,
            project_dir=project_dir,
        )

    @classmethod
    def from_spec_file(cls, spec_path: Path) -> CompositionProject:
        """Load a project from a single spec file (no project directory).

        Useful for standalone spec files and templates. Intent and trajectory
        use defaults.

        Args:
            spec_path: Path to a composition.yaml file.

        Returns:
            A CompositionProject with default intent and trajectory.
        """
        spec = load_composition_spec_auto(spec_path)
        return cls(
            spec=spec,
            intent=IntentSpec(text="", keywords=[]),
            trajectory=MultiDimensionalTrajectory.default(),
            project_dir=spec_path.parent,
        )

    @property
    def title(self) -> str:
        """Return the project title from the spec."""
        if isinstance(self.spec, CompositionSpecV2):
            return self.spec.identity.title
        return self.spec.title
