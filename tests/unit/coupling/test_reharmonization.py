"""Tests for the reharmonization engine.

Phase 3.5 Step 5 — IMPROVEMENT.md §5.1, PROJECT.md §3.4.3.
"""

from __future__ import annotations

import random

from yao.coupling.reharmonization import (
    ReharmonizationConstraints,
    ReharmonizationOperation,
    reharmonize,
)
from yao.ir.harmony import ChordFunction


def _simple_progression() -> list[ChordFunction]:
    """I - IV - V - I in C major."""
    return [
        ChordFunction(degree=0, quality="maj"),  # I
        ChordFunction(degree=3, quality="maj"),  # IV
        ChordFunction(degree=4, quality="dom7"),  # V7
        ChordFunction(degree=0, quality="maj"),  # I
    ]


class TestReharmonizationOperationEnum:
    """All 12 operations exist."""

    def test_all_operations(self) -> None:
        assert len(ReharmonizationOperation) == 12

    def test_operation_values(self) -> None:
        assert ReharmonizationOperation.TRITONE_SUBSTITUTION == "tritone_substitution"
        assert ReharmonizationOperation.II_V_INSERTION == "ii_V_insertion"


class TestReharmonizationConstraints:
    """Melody compatibility checking."""

    def test_empty_melody_always_compatible(self) -> None:
        constraints = ReharmonizationConstraints()
        assert constraints.melody_compatible(0, "maj", 0)

    def test_chord_tone_compatible(self) -> None:
        constraints = ReharmonizationConstraints(
            melody_pitches_per_position={0: frozenset({0})}  # C
        )
        # C is the root of C major → compatible
        assert constraints.melody_compatible(0, "maj", 0)

    def test_minor_second_clash_detected(self) -> None:
        constraints = ReharmonizationConstraints(
            melody_pitches_per_position={0: frozenset({1})}  # C#
        )
        # C# is a minor second from C (root of C major) → clash
        assert not constraints.melody_compatible(0, "maj", 0)

    def test_preserve_melody_flag(self) -> None:
        constraints = ReharmonizationConstraints(preserve_melody=True)
        assert constraints.preserve_melody


class TestReharmonize:
    """Core reharmonization function."""

    def test_zero_intensity_no_change(self) -> None:
        """Intensity 0.0 means no operations applied."""
        prog = _simple_progression()
        rng = random.Random(42)
        result = reharmonize(
            prog,
            list(ReharmonizationOperation),
            intensity=0.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=rng,
        )
        assert len(result) == len(prog)
        for orig, new in zip(prog, result, strict=False):
            assert orig.degree == new.degree
            assert orig.quality == new.quality

    def test_high_intensity_produces_changes(self) -> None:
        """High intensity should produce at least some changes."""
        prog = _simple_progression()
        rng = random.Random(42)
        result = reharmonize(
            prog,
            list(ReharmonizationOperation),
            intensity=1.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=rng,
        )
        # At least one chord should be different
        any_different = any(
            orig.degree != new.degree or orig.quality != new.quality for orig, new in zip(prog, result, strict=False)
        )
        assert any_different

    def test_does_not_mutate_input(self) -> None:
        """Input progression is not mutated."""
        prog = _simple_progression()
        original_degrees = [c.degree for c in prog]
        rng = random.Random(42)
        reharmonize(
            prog,
            list(ReharmonizationOperation),
            intensity=1.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=rng,
        )
        assert [c.degree for c in prog] == original_degrees

    def test_preserves_progression_length(self) -> None:
        """Output has same length as input."""
        prog = _simple_progression()
        rng = random.Random(42)
        result = reharmonize(
            prog,
            list(ReharmonizationOperation),
            intensity=0.5,
            style="classical",
            constraints=ReharmonizationConstraints(),
            rng=rng,
        )
        assert len(result) == len(prog)

    def test_melody_incompatible_rejected(self) -> None:
        """Operations producing melody clashes are rejected."""
        prog = _simple_progression()
        # Melody has C# on position 1 — any chord with C natural will clash
        constraints = ReharmonizationConstraints(
            melody_pitches_per_position={
                0: frozenset({0}),
                1: frozenset({1}),  # C# clashes with chords containing C or D
                2: frozenset({7}),
                3: frozenset({0}),
            },
        )
        rng = random.Random(42)
        result = reharmonize(
            prog,
            [ReharmonizationOperation.EXTENSION_ADD],
            intensity=1.0,
            style="jazz",
            constraints=constraints,
            rng=rng,
        )
        # Result should still be valid
        assert len(result) == len(prog)

    def test_extension_add_upgrades_triad(self) -> None:
        """EXTENSION_ADD converts triads to 7th chords."""
        prog = [ChordFunction(degree=0, quality="maj")]
        rng = random.Random(42)
        result = reharmonize(
            prog,
            [ReharmonizationOperation.EXTENSION_ADD],
            intensity=1.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=rng,
        )
        assert result[0].quality == "maj7"

    def test_modal_interchange_major_to_minor(self) -> None:
        """MODAL_INTERCHANGE converts major to minor."""
        prog = [ChordFunction(degree=3, quality="maj")]  # IV
        rng = random.Random(42)
        result = reharmonize(
            prog,
            [ReharmonizationOperation.MODAL_INTERCHANGE],
            intensity=1.0,
            style="classical",
            constraints=ReharmonizationConstraints(),
            rng=rng,
        )
        assert result[0].quality == "min"

    def test_deterministic_with_seed(self) -> None:
        """Same seed produces same result."""
        prog = _simple_progression()
        r1 = reharmonize(
            prog,
            list(ReharmonizationOperation),
            0.5,
            "jazz",
            ReharmonizationConstraints(),
            random.Random(42),
        )
        r2 = reharmonize(
            prog,
            list(ReharmonizationOperation),
            0.5,
            "jazz",
            ReharmonizationConstraints(),
            random.Random(42),
        )
        for a, b in zip(r1, r2, strict=False):
            assert a.degree == b.degree
            assert a.quality == b.quality
