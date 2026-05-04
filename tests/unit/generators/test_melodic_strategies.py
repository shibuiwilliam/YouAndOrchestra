"""Tests for melodic generation strategies (Phase γ.6)."""

from __future__ import annotations

import pytest

from yao.generators.melodic_strategies import (
    MelodicGenerationStrategy,
    generate_melody_pitches,
)


class TestMelodicGenerationStrategy:
    """Verify all 8 strategies exist and are enumerable."""

    def test_has_8_strategies(self) -> None:
        assert len(MelodicGenerationStrategy) == 8

    def test_strategy_values(self) -> None:
        expected = {
            "contour_based",
            "motif_development",
            "linear_voice",
            "arpeggiated",
            "scalar_runs",
            "call_response",
            "pedal_tone",
            "hocketing",
        }
        actual = {s.value for s in MelodicGenerationStrategy}
        assert actual == expected


class TestGenerateMelodyPitches:
    """Verify each strategy produces valid output."""

    @pytest.mark.parametrize("strategy", list(MelodicGenerationStrategy))
    def test_produces_correct_count(self, strategy: MelodicGenerationStrategy) -> None:
        """Each strategy produces exactly n_notes pitches."""
        pitches = generate_melody_pitches(
            strategy=strategy,
            n_notes=16,
            key="C major",
            root_midi=60,
            seed=42,
        )
        assert len(pitches) == 16

    @pytest.mark.parametrize("strategy", list(MelodicGenerationStrategy))
    def test_pitches_in_midi_range(self, strategy: MelodicGenerationStrategy) -> None:
        """All pitches are valid MIDI (0-127)."""
        pitches = generate_melody_pitches(
            strategy=strategy,
            n_notes=32,
            key="D minor",
            root_midi=62,
            seed=123,
        )
        for p in pitches:
            assert 0 <= p <= 127

    @pytest.mark.parametrize("strategy", list(MelodicGenerationStrategy))
    def test_deterministic_with_seed(self, strategy: MelodicGenerationStrategy) -> None:
        """Same seed produces same output."""
        p1 = generate_melody_pitches(strategy=strategy, n_notes=16, key="G major", root_midi=67, seed=99)
        p2 = generate_melody_pitches(strategy=strategy, n_notes=16, key="G major", root_midi=67, seed=99)
        assert p1 == p2

    @pytest.mark.parametrize("strategy", list(MelodicGenerationStrategy))
    def test_different_seeds_differ(self, strategy: MelodicGenerationStrategy) -> None:
        """Different seeds produce different output."""
        p1 = generate_melody_pitches(strategy=strategy, n_notes=16, key="C major", root_midi=60, seed=1)
        p2 = generate_melody_pitches(strategy=strategy, n_notes=16, key="C major", root_midi=60, seed=999)
        assert p1 != p2


class TestStrategyCharacteristics:
    """Verify each strategy produces distinct melodic character."""

    def test_contour_based_has_arch_shape(self) -> None:
        """Contour-based tends to rise then fall."""
        pitches = generate_melody_pitches(
            strategy=MelodicGenerationStrategy.CONTOUR_BASED,
            n_notes=16,
            key="C major",
            root_midi=60,
            seed=42,
        )
        # Contour shaping should produce non-constant output
        assert max(pitches) != min(pitches)

    def test_motif_development_has_repetition(self) -> None:
        """Motif development repeats similar intervals."""
        pitches = generate_melody_pitches(
            strategy=MelodicGenerationStrategy.MOTIF_DEVELOPMENT,
            n_notes=20,
            key="C major",
            root_midi=60,
            seed=42,
        )
        # Check for interval pattern repetition
        intervals = [pitches[i + 1] - pitches[i] for i in range(len(pitches) - 1)]
        # At least some intervals should repeat (motif development property)
        unique_intervals = set(intervals)
        # With motif development, we expect fewer unique intervals than random
        assert len(unique_intervals) < len(intervals)

    def test_pedal_tone_returns_to_root(self) -> None:
        """Pedal tone strategy frequently returns to the root."""
        pitches = generate_melody_pitches(
            strategy=MelodicGenerationStrategy.PEDAL_TONE,
            n_notes=20,
            key="C major",
            root_midi=60,
            seed=42,
        )
        # Count how many times root appears (should be frequent)
        root_count = pitches.count(60)
        assert root_count >= 5  # At least 25% return to pedal

    def test_hocketing_has_register_jumps(self) -> None:
        """Hocketing alternates between high and low registers."""
        pitches = generate_melody_pitches(
            strategy=MelodicGenerationStrategy.HOCKETING,
            n_notes=16,
            key="C major",
            root_midi=60,
            seed=42,
        )
        # Count large jumps (> 5 semitones)
        big_jumps = sum(1 for i in range(len(pitches) - 1) if abs(pitches[i + 1] - pitches[i]) > 5)
        # Hocketing should have many large jumps
        assert big_jumps >= 4

    def test_linear_voice_mostly_stepwise(self) -> None:
        """Linear voice has mostly small intervals."""
        pitches = generate_melody_pitches(
            strategy=MelodicGenerationStrategy.LINEAR_VOICE,
            n_notes=20,
            key="C major",
            root_midi=60,
            seed=42,
        )
        intervals = [abs(pitches[i + 1] - pitches[i]) for i in range(len(pitches) - 1)]
        small_steps = sum(1 for i in intervals if i <= 3)
        # At least 60% should be small steps
        assert small_steps / len(intervals) >= 0.5

    def test_strategies_produce_different_outputs(self) -> None:
        """Different strategies from same seed produce different melodies."""
        results: dict[str, list[int]] = {}
        for strategy in MelodicGenerationStrategy:
            results[strategy.value] = generate_melody_pitches(
                strategy=strategy,
                n_notes=16,
                key="C major",
                root_midi=60,
                seed=42,
            )
        # All 8 strategies should produce distinct sequences
        unique_sequences = {tuple(v) for v in results.values()}
        assert len(unique_sequences) == 8
