"""Tests for six-phase cognitive protocol — PR-6.

Verifies that:
- Phase ordering is correct (1-6)
- PhaseIncompleteError is raised when required artifacts are missing
- Phase transitions are validated
- --force-phase concept (force=True bypasses checks with warning)
"""

from __future__ import annotations

import warnings

import pytest

from yao.conductor.protocol import (
    PHASE_REQUIRED_ARTIFACTS,
    Phase,
    check_phase_artifacts,
    get_previous_phase,
    get_required_artifacts,
    validate_phase_transition,
)
from yao.errors import PhaseIncompleteError


class TestPhaseEnum:
    """Test Phase IntEnum structure."""

    def test_phase_ordering(self) -> None:
        """Phases are numbered 1-6 in correct order."""
        assert Phase.INTENT_CRYSTALLIZATION == 1
        assert Phase.ARCHITECTURAL_SKETCH == 2
        assert Phase.SKELETAL_GENERATION == 3
        assert Phase.CRITIC_COMPOSER_DIALOGUE == 4
        assert Phase.DETAILED_FILLING == 5
        assert Phase.LISTENING_SIMULATION == 6

    def test_phase_count(self) -> None:
        """There are exactly 6 phases."""
        assert len(Phase) == 6

    def test_phases_are_sequential(self) -> None:
        """Phase values form a contiguous sequence from 1 to 6."""
        values = sorted(p.value for p in Phase)
        assert values == [1, 2, 3, 4, 5, 6]

    def test_phase_comparison(self) -> None:
        """Phases can be compared (IntEnum)."""
        assert Phase.INTENT_CRYSTALLIZATION < Phase.ARCHITECTURAL_SKETCH
        assert Phase.LISTENING_SIMULATION > Phase.DETAILED_FILLING


class TestPhaseRequiredArtifacts:
    """Test PHASE_REQUIRED_ARTIFACTS mapping."""

    def test_all_phases_have_artifacts(self) -> None:
        """Every phase has at least one required artifact."""
        for phase in Phase:
            assert phase in PHASE_REQUIRED_ARTIFACTS
            assert len(PHASE_REQUIRED_ARTIFACTS[phase]) > 0

    def test_intent_crystallization_artifacts(self) -> None:
        """Phase 1 requires intent.md."""
        artifacts = PHASE_REQUIRED_ARTIFACTS[Phase.INTENT_CRYSTALLIZATION]
        assert "intent.md" in artifacts

    def test_architectural_sketch_artifacts(self) -> None:
        """Phase 2 requires trajectory.yaml."""
        artifacts = PHASE_REQUIRED_ARTIFACTS[Phase.ARCHITECTURAL_SKETCH]
        assert "trajectory.yaml" in artifacts

    def test_skeletal_generation_artifacts(self) -> None:
        """Phase 3 requires score_skeleton.json."""
        artifacts = PHASE_REQUIRED_ARTIFACTS[Phase.SKELETAL_GENERATION]
        assert "score_skeleton.json" in artifacts

    def test_critic_composer_dialogue_artifacts(self) -> None:
        """Phase 4 requires critique and selected skeleton."""
        artifacts = PHASE_REQUIRED_ARTIFACTS[Phase.CRITIC_COMPOSER_DIALOGUE]
        assert "critique_round_1.md" in artifacts
        assert "selected_skeleton.json" in artifacts

    def test_detailed_filling_artifacts(self) -> None:
        """Phase 5 requires MIDI and stems."""
        artifacts = PHASE_REQUIRED_ARTIFACTS[Phase.DETAILED_FILLING]
        assert "full.mid" in artifacts
        assert "stems/" in artifacts

    def test_listening_simulation_artifacts(self) -> None:
        """Phase 6 requires analysis, evaluation, and critique."""
        artifacts = PHASE_REQUIRED_ARTIFACTS[Phase.LISTENING_SIMULATION]
        assert "analysis.json" in artifacts
        assert "evaluation.json" in artifacts
        assert "critique.md" in artifacts


class TestGetRequiredArtifacts:
    """Test get_required_artifacts helper."""

    def test_returns_copy(self) -> None:
        """Returns a copy, not the original list."""
        artifacts = get_required_artifacts(Phase.INTENT_CRYSTALLIZATION)
        artifacts.append("extra.txt")
        assert "extra.txt" not in PHASE_REQUIRED_ARTIFACTS[Phase.INTENT_CRYSTALLIZATION]


class TestGetPreviousPhase:
    """Test get_previous_phase helper."""

    def test_first_phase_has_no_previous(self) -> None:
        """Phase 1 has no predecessor."""
        assert get_previous_phase(Phase.INTENT_CRYSTALLIZATION) is None

    def test_second_phase_previous_is_first(self) -> None:
        """Phase 2's predecessor is Phase 1."""
        assert get_previous_phase(Phase.ARCHITECTURAL_SKETCH) == Phase.INTENT_CRYSTALLIZATION

    def test_last_phase_previous(self) -> None:
        """Phase 6's predecessor is Phase 5."""
        assert get_previous_phase(Phase.LISTENING_SIMULATION) == Phase.DETAILED_FILLING


class TestCheckPhaseArtifacts:
    """Test check_phase_artifacts enforcement."""

    def test_raises_when_artifact_missing(self) -> None:
        """PhaseIncompleteError raised when required artifact is absent."""
        with pytest.raises(PhaseIncompleteError) as exc_info:
            check_phase_artifacts(Phase.INTENT_CRYSTALLIZATION, set())

        assert exc_info.value.phase == "INTENT_CRYSTALLIZATION"
        assert "intent.md" in exc_info.value.missing_artifacts

    def test_passes_when_all_artifacts_present(self) -> None:
        """No error when all required artifacts exist."""
        check_phase_artifacts(
            Phase.INTENT_CRYSTALLIZATION,
            {"intent.md"},
        )

    def test_raises_with_partial_artifacts(self) -> None:
        """PhaseIncompleteError lists only the missing ones."""
        with pytest.raises(PhaseIncompleteError) as exc_info:
            check_phase_artifacts(
                Phase.CRITIC_COMPOSER_DIALOGUE,
                {"critique_round_1.md"},  # missing selected_skeleton.json
            )

        assert "selected_skeleton.json" in exc_info.value.missing_artifacts
        assert "critique_round_1.md" not in exc_info.value.missing_artifacts

    def test_phase_5_requires_both_midi_and_stems(self) -> None:
        """Phase 5 needs both full.mid and stems/."""
        with pytest.raises(PhaseIncompleteError) as exc_info:
            check_phase_artifacts(
                Phase.DETAILED_FILLING,
                {"full.mid"},  # missing stems/
            )

        assert "stems/" in exc_info.value.missing_artifacts

    def test_phase_6_all_present(self) -> None:
        """Phase 6 passes with all three artifacts."""
        check_phase_artifacts(
            Phase.LISTENING_SIMULATION,
            {"analysis.json", "evaluation.json", "critique.md"},
        )


class TestValidatePhaseTransition:
    """Test validate_phase_transition enforcement."""

    def test_sequential_transition_allowed(self) -> None:
        """Moving from phase N to phase N+1 is allowed."""
        # Should not raise
        validate_phase_transition(
            Phase.INTENT_CRYSTALLIZATION,
            Phase.ARCHITECTURAL_SKETCH,
        )

    def test_skipping_phase_raises(self) -> None:
        """Skipping a phase raises PhaseIncompleteError."""
        with pytest.raises(PhaseIncompleteError) as exc_info:
            validate_phase_transition(
                Phase.INTENT_CRYSTALLIZATION,
                Phase.SKELETAL_GENERATION,  # skips phase 2
            )

        assert "Cannot skip" in str(exc_info.value)

    def test_backward_transition_raises(self) -> None:
        """Going backward raises PhaseIncompleteError."""
        with pytest.raises(PhaseIncompleteError):
            validate_phase_transition(
                Phase.DETAILED_FILLING,
                Phase.SKELETAL_GENERATION,
            )

    def test_force_allows_skip_with_warning(self) -> None:
        """force=True allows skipping but emits a warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_phase_transition(
                Phase.INTENT_CRYSTALLIZATION,
                Phase.SKELETAL_GENERATION,
                force=True,
            )

        assert len(w) == 1
        assert "debug only" in str(w[0].message).lower()

    def test_force_allows_backward_with_warning(self) -> None:
        """force=True allows backward transition with warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_phase_transition(
                Phase.LISTENING_SIMULATION,
                Phase.INTENT_CRYSTALLIZATION,
                force=True,
            )

        assert len(w) == 1


class TestPhaseIncompleteError:
    """Test PhaseIncompleteError exception class."""

    def test_error_attributes(self) -> None:
        """PhaseIncompleteError stores phase and missing_artifacts."""
        err = PhaseIncompleteError(
            phase="ARCHITECTURAL_SKETCH",
            missing_artifacts=["trajectory.yaml"],
        )

        assert err.phase == "ARCHITECTURAL_SKETCH"
        assert err.missing_artifacts == ["trajectory.yaml"]
        assert "ARCHITECTURAL_SKETCH" in str(err)
        assert "trajectory.yaml" in str(err)

    def test_error_is_yao_error(self) -> None:
        """PhaseIncompleteError is a YaOError subclass."""
        from yao.errors import YaOError

        err = PhaseIncompleteError(phase="TEST", missing_artifacts=[])
        assert isinstance(err, YaOError)

    def test_custom_message(self) -> None:
        """PhaseIncompleteError can take a custom message."""
        err = PhaseIncompleteError(
            phase="TEST",
            missing_artifacts=[],
            message="Custom error message",
        )
        assert str(err) == "Custom error message"
