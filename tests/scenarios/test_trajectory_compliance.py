"""Trajectory compliance tests — verify generators respond to trajectory changes.

These tests document the gap between v1 (velocity-only response) and v2
(multi-dimensional response). Tests that fail due to known v1 limitations
are marked with xfail.

See CLAUDE.md Rule #7: "Trajectory is a control signal, not a decoration."
"""

from __future__ import annotations

import pytest

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.registry import get_generator
from yao.ir.score_ir import ScoreIR
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.trajectory import TrajectoryDimension, TrajectorySpec


def _make_spec(seed: int = 42) -> CompositionSpec:
    """Create a standard test spec."""
    return CompositionSpec(
        title="Trajectory Compliance Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[
            SectionSpec(name="main", bars=8, dynamics="mf"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=seed, temperature=0.5),
    )


def _uniform_trajectory(tension: float, density: float = 0.5) -> TrajectorySpec:
    """Create a trajectory with uniform values across all bars."""
    return TrajectorySpec(
        tension=TrajectoryDimension(type="linear", target=tension),
        density=TrajectoryDimension(type="linear", target=density),
        predictability=TrajectoryDimension(type="linear", target=0.5),
    )


def _avg_velocity(score: ScoreIR) -> float:
    """Compute average velocity across all notes."""
    notes = [n for s in score.sections for p in s.parts for n in p.notes]
    if not notes:
        return 0.0
    return sum(n.velocity for n in notes) / len(notes)


def _max_pitch(score: ScoreIR) -> int:
    """Compute max pitch across all notes."""
    notes = [n for s in score.sections for p in s.parts for n in p.notes]
    if not notes:
        return 0
    return max(n.pitch for n in notes)


def _min_pitch(score: ScoreIR) -> int:
    """Compute min pitch across all notes."""
    notes = [n for s in score.sections for p in s.parts for n in p.notes]
    if not notes:
        return 127
    return min(n.pitch for n in notes)


def _count_leaps(score: ScoreIR, threshold: int = 4) -> int:
    """Count melodic leaps (intervals >= threshold semitones)."""
    count = 0
    for section in score.sections:
        for part in section.parts:
            for i in range(1, len(part.notes)):
                interval = abs(part.notes[i].pitch - part.notes[i - 1].pitch)
                if interval >= threshold:
                    count += 1
    return count


def _note_count(score: ScoreIR) -> int:
    """Count total notes."""
    return sum(len(p.notes) for s in score.sections for p in s.parts)


class TestVelocityRespondsToTension:
    """V1 generators respond to tension via velocity — this should PASS."""

    def test_stochastic_velocity_higher_at_high_tension(self) -> None:
        spec = _make_spec()
        gen = get_generator("stochastic")

        score_low, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.1))
        score_high, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.9))

        avg_low = _avg_velocity(score_low)
        avg_high = _avg_velocity(score_high)
        assert avg_high > avg_low + 5, (
            f"High tension velocity ({avg_high:.1f}) should be notably higher than low tension ({avg_low:.1f})"
        )

    def test_rule_based_velocity_higher_at_high_tension(self) -> None:
        spec = CompositionSpec(
            title="Rule Based Tension Test",
            key="C major",
            tempo_bpm=120.0,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="main", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="rule_based"),
        )
        gen = get_generator("rule_based")

        score_low, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.1))
        score_high, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.9))

        avg_low = _avg_velocity(score_low)
        avg_high = _avg_velocity(score_high)
        assert avg_high > avg_low + 5


class TestPitchRespondsToTension:
    """V2: higher tension should push melodies to higher register.

    Implemented: stochastic generator biases upward motion at high tension.
    """

    def test_stochastic_higher_register_at_high_tension(self) -> None:
        spec = _make_spec()
        gen = get_generator("stochastic")

        score_low, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.1))
        score_high, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.9))

        assert _max_pitch(score_high) > _max_pitch(score_low), "High tension should push melody to higher register"


class TestLeapsRespondToTension:
    """V2: higher tension should produce more melodic leaps.

    Implemented: stochastic generator increases leap probability at high tension.
    """

    def test_stochastic_more_leaps_at_high_tension(self) -> None:
        spec = _make_spec()
        gen = get_generator("stochastic")

        score_low, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.1))
        score_high, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.9))

        assert _count_leaps(score_high) > _count_leaps(score_low), "High tension should produce more melodic leaps"


class TestDensityRespondsToTrajectory:
    """V2: higher density trajectory should produce more notes.

    Implemented: stochastic generator uses density-aware rhythm selection.
    """

    def test_stochastic_more_notes_at_high_density(self) -> None:
        spec = _make_spec()
        gen = get_generator("stochastic")

        score_sparse, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.5, density=0.1))
        score_dense, _ = gen.generate(spec, trajectory=_uniform_trajectory(0.5, density=0.9))

        assert _note_count(score_dense) > _note_count(score_sparse), "High density trajectory should produce more notes"


class TestNoDifferenceBetweenIgnoredDimensions:
    """Verify that dimensions currently ignored produce identical output.

    This test passes NOW and should FAIL when generators start responding
    to brightness/register_height (meaning we need to update this test).
    """

    def test_brightness_currently_ignored(self) -> None:
        spec = _make_spec()
        gen = get_generator("stochastic")

        traj_a = TrajectorySpec(
            tension=TrajectoryDimension(type="linear", target=0.5),
            brightness=TrajectoryDimension(type="linear", target=0.1),
        )
        traj_b = TrajectorySpec(
            tension=TrajectoryDimension(type="linear", target=0.5),
            brightness=TrajectoryDimension(type="linear", target=0.9),
        )
        score_a, _ = gen.generate(spec, trajectory=traj_a)
        score_b, _ = gen.generate(spec, trajectory=traj_b)

        # Same seed + same tension = same output (brightness ignored)
        assert _avg_velocity(score_a) == pytest.approx(_avg_velocity(score_b), abs=1)
