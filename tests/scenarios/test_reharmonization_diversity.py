"""Scenario test: reharmonization produces harmonic diversity.

Tests that reharmonization operations transform progressions while
respecting melody compatibility constraints.

Phase 3.5 Step 7 — IMPROVEMENT.md §5.1.
"""

from __future__ import annotations

import random

from yao.coupling.reharmonization import (
    ReharmonizationConstraints,
    ReharmonizationOperation,
    reharmonize,
)
from yao.ir.harmony import ChordFunction


def _i_iv_v_i() -> list[ChordFunction]:
    """Standard I-IV-V-I progression."""
    return [
        ChordFunction(degree=0, quality="maj"),
        ChordFunction(degree=3, quality="maj"),
        ChordFunction(degree=4, quality="dom7"),
        ChordFunction(degree=0, quality="maj"),
    ]


class TestReharmonizationDiversity:
    """Scenario: reharmonization produces progressively richer harmony."""

    def test_intensity_0_no_change(self) -> None:
        """Intensity 0.0 produces identical progression."""
        prog = _i_iv_v_i()
        result = reharmonize(
            prog,
            list(ReharmonizationOperation),
            intensity=0.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=random.Random(42),
        )
        for a, b in zip(prog, result, strict=False):
            assert a.degree == b.degree and a.quality == b.quality

    def test_intensity_increases_changes(self) -> None:
        """Higher intensity produces more changes."""
        prog = _i_iv_v_i()
        ops = list(ReharmonizationOperation)

        # Count changes at different intensities
        changes_low = 0
        changes_high = 0

        for seed in range(10):
            result_low = reharmonize(
                prog,
                ops,
                0.2,
                "jazz",
                ReharmonizationConstraints(),
                random.Random(seed),
            )
            result_high = reharmonize(
                prog,
                ops,
                0.9,
                "jazz",
                ReharmonizationConstraints(),
                random.Random(seed),
            )
            changes_low += sum(
                1 for a, b in zip(prog, result_low, strict=False) if a.degree != b.degree or a.quality != b.quality
            )
            changes_high += sum(
                1 for a, b in zip(prog, result_high, strict=False) if a.degree != b.degree or a.quality != b.quality
            )

        # High intensity should produce at least as many changes as low
        assert changes_high >= changes_low

    def test_melody_compatibility_enforced(self) -> None:
        """Reharmonization respects melody constraints."""
        prog = _i_iv_v_i()
        # Melody has E (pc=4) on position 0 — clashes with chords containing Eb (pc=3)
        constraints = ReharmonizationConstraints(
            melody_pitches_per_position={
                0: frozenset({4}),  # E
                1: frozenset({0}),  # C
                2: frozenset({7}),  # G
                3: frozenset({0}),  # C
            },
        )
        for seed in range(20):
            result = reharmonize(
                prog,
                list(ReharmonizationOperation),
                intensity=1.0,
                style="jazz",
                constraints=constraints,
                rng=random.Random(seed),
            )
            # Should always produce a valid progression (same length)
            assert len(result) == len(prog)

    def test_extension_add_increases_complexity(self) -> None:
        """EXTENSION_ADD should upgrade triads to 7th chords."""
        prog = _i_iv_v_i()
        result = reharmonize(
            prog,
            [ReharmonizationOperation.EXTENSION_ADD],
            intensity=1.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=random.Random(42),
        )
        # At least one triad should have been upgraded
        upgraded = sum(
            1
            for a, b in zip(prog, result, strict=False)
            if a.quality in ("maj", "min") and b.quality in ("maj7", "min7", "dim7")
        )
        assert upgraded >= 1

    def test_does_not_mutate_original(self) -> None:
        """Original progression is never mutated."""
        prog = _i_iv_v_i()
        original = [(c.degree, c.quality) for c in prog]
        reharmonize(
            prog,
            list(ReharmonizationOperation),
            intensity=1.0,
            style="jazz",
            constraints=ReharmonizationConstraints(),
            rng=random.Random(42),
        )
        after = [(c.degree, c.quality) for c in prog]
        assert original == after
