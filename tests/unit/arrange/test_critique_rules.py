"""Tests for arrangement-specific critique rules."""

from __future__ import annotations

from yao.arrange.critique_rules import (
    check_chord_function_consistency,
    check_hook_fidelity,
    check_melody_preservation,
    check_transformation_strength,
)
from yao.arrange.style_vector_ops import PreservationResult


def _make_preservation(
    melody: float = 0.9,
    hook: float = 0.85,
    chord: float = 0.80,
    form: bool = True,
) -> PreservationResult:
    return PreservationResult(
        melody_similarity=melody,
        hook_similarity=hook,
        chord_similarity=chord,
        form_preserved=form,
        all_passed=True,
        violations=(),
    )


class TestMelodyPreservation:
    def test_passes_above_threshold(self) -> None:
        passed, _ = check_melody_preservation(_make_preservation(melody=0.9))
        assert passed

    def test_fails_below_threshold(self) -> None:
        passed, msg = check_melody_preservation(_make_preservation(melody=0.5))
        assert not passed
        assert "below" in msg


class TestHookFidelity:
    def test_passes_above_threshold(self) -> None:
        passed, _ = check_hook_fidelity(_make_preservation(hook=0.85))
        assert passed

    def test_fails_below_threshold(self) -> None:
        passed, _ = check_hook_fidelity(_make_preservation(hook=0.5))
        assert not passed


class TestChordFunctionConsistency:
    def test_passes_above_threshold(self) -> None:
        passed, _ = check_chord_function_consistency(_make_preservation(chord=0.8))
        assert passed

    def test_fails_below_threshold(self) -> None:
        passed, _ = check_chord_function_consistency(_make_preservation(chord=0.3))
        assert not passed


class TestTransformationStrength:
    def test_passes_with_change(self) -> None:
        passed, _ = check_transformation_strength(_make_preservation(melody=0.9, hook=0.85, chord=0.5))
        assert passed

    def test_fails_identity(self) -> None:
        passed, _ = check_transformation_strength(_make_preservation(melody=1.0, hook=1.0, chord=1.0, form=True))
        assert not passed
