"""Arrangement-specific critique rules.

Four rules that evaluate arrangement quality:
1. MelodyPreservationRule — is the melody preserved?
2. HookFidelityRule — is the hook recognizable?
3. ChordFunctionConsistencyRule — do chords still function?
4. TransformationStrengthRule — was anything actually changed?

These complement the existing 15 general critique rules.

Belongs to arrange/ package (Layer 6 consumer).
"""

from __future__ import annotations

from yao.arrange.style_vector_ops import PreservationResult


def check_melody_preservation(
    preservation: PreservationResult,
    threshold: float = 0.85,
) -> tuple[bool, str]:
    """Check if melody is sufficiently preserved.

    Args:
        preservation: The preservation result.
        threshold: Minimum similarity.

    Returns:
        Tuple of (passed, message).
    """
    passed = preservation.melody_similarity >= threshold
    msg = (
        f"Melody similarity {preservation.melody_similarity:.2f} {'meets' if passed else 'below'} threshold {threshold}"
    )
    return passed, msg


def check_hook_fidelity(
    preservation: PreservationResult,
    threshold: float = 0.80,
) -> tuple[bool, str]:
    """Check if the rhythmic hook is preserved.

    Args:
        preservation: The preservation result.
        threshold: Minimum similarity.

    Returns:
        Tuple of (passed, message).
    """
    passed = preservation.hook_similarity >= threshold
    msg = f"Hook similarity {preservation.hook_similarity:.2f} {'meets' if passed else 'below'} threshold {threshold}"
    return passed, msg


def check_chord_function_consistency(
    preservation: PreservationResult,
    threshold: float = 0.75,
) -> tuple[bool, str]:
    """Check if chord functions are consistent.

    Args:
        preservation: The preservation result.
        threshold: Minimum similarity.

    Returns:
        Tuple of (passed, message).
    """
    passed = preservation.chord_similarity >= threshold
    msg = (
        f"Chord function similarity {preservation.chord_similarity:.2f} "
        f"{'meets' if passed else 'below'} threshold {threshold}"
    )
    return passed, msg


def check_transformation_strength(
    preservation: PreservationResult,
    min_change: float = 0.05,
) -> tuple[bool, str]:
    """Check that the arrangement actually changed something meaningful.

    If everything is identical, the arrangement didn't do anything.

    Args:
        preservation: The preservation result.
        min_change: Minimum expected change (1 - similarity).

    Returns:
        Tuple of (passed, message).
    """
    avg_change = (
        1.0 - (preservation.melody_similarity + preservation.hook_similarity + preservation.chord_similarity) / 3.0
    )

    passed = avg_change >= min_change or not preservation.form_preserved
    msg = f"Average transformation strength {avg_change:.2f} {'meets' if passed else 'below'} minimum {min_change}"
    return passed, msg
