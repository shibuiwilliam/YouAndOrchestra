"""Six-Phase Cognitive Protocol Enforcement.

Defines the six phases of composition and enforces that required artifacts
exist before advancing to the next phase. See CLAUDE.md §11.
"""

from __future__ import annotations

from enum import IntEnum


class Phase(IntEnum):
    """The six cognitive phases of composition in YaO.

    Each phase must produce specific artifacts before the next phase
    can begin. Phases are ordered; skipping is not allowed in production.
    """

    INTENT_CRYSTALLIZATION = 1
    ARCHITECTURAL_SKETCH = 2
    SKELETAL_GENERATION = 3
    CRITIC_COMPOSER_DIALOGUE = 4
    DETAILED_FILLING = 5
    LISTENING_SIMULATION = 6


PHASE_REQUIRED_ARTIFACTS: dict[Phase, list[str]] = {
    Phase.INTENT_CRYSTALLIZATION: ["intent.md"],
    Phase.ARCHITECTURAL_SKETCH: ["trajectory.yaml"],
    Phase.SKELETAL_GENERATION: ["score_skeleton.json"],
    Phase.CRITIC_COMPOSER_DIALOGUE: ["critique_round_1.md", "selected_skeleton.json"],
    Phase.DETAILED_FILLING: ["full.mid", "stems/"],
    Phase.LISTENING_SIMULATION: ["analysis.json", "evaluation.json", "critique.md"],
}


def get_required_artifacts(phase: Phase) -> list[str]:
    """Return the list of required artifacts for a given phase.

    Args:
        phase: The phase to query.

    Returns:
        List of artifact file/directory names that must exist after this phase completes.
    """
    return list(PHASE_REQUIRED_ARTIFACTS[phase])


def get_previous_phase(phase: Phase) -> Phase | None:
    """Return the phase that must complete before the given phase.

    Args:
        phase: The current phase.

    Returns:
        The previous phase, or None if this is the first phase.
    """
    if phase == Phase.INTENT_CRYSTALLIZATION:
        return None
    return Phase(phase.value - 1)


def validate_phase_transition(
    current_phase: Phase,
    target_phase: Phase,
    *,
    force: bool = False,
) -> None:
    """Validate that a phase transition is allowed.

    Phases must be advanced sequentially. Skipping phases is forbidden
    unless force=True (debug-only, emits warning).

    Args:
        current_phase: The phase that has just completed.
        target_phase: The phase to advance to.
        force: If True, allow skipping (debug only).

    Raises:
        PhaseIncompleteError: If the transition is not allowed.
    """
    from yao.errors import PhaseIncompleteError

    if force:
        import warnings

        warnings.warn(
            f"Forcing phase transition from {current_phase.name} to {target_phase.name}. This is for debug only.",
            stacklevel=2,
        )
        return

    expected_next = current_phase.value + 1
    if target_phase.value != expected_next:
        raise PhaseIncompleteError(
            phase=current_phase.name,
            missing_artifacts=[],
            message=(f"Cannot skip from {current_phase.name} to {target_phase.name}. Must advance sequentially."),
        )


def check_phase_artifacts(
    phase: Phase,
    existing_artifacts: set[str],
) -> None:
    """Check that all required artifacts for a phase exist.

    Args:
        phase: The phase whose artifacts to check.
        existing_artifacts: Set of artifact names that currently exist.

    Raises:
        PhaseIncompleteError: If any required artifact is missing.
    """
    from yao.errors import PhaseIncompleteError

    required = PHASE_REQUIRED_ARTIFACTS[phase]
    missing = [a for a in required if a not in existing_artifacts]

    if missing:
        raise PhaseIncompleteError(
            phase=phase.name,
            missing_artifacts=missing,
        )
