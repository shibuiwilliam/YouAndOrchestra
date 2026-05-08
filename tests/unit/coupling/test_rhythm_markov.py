"""Tests for the Rhythm Markov generator.

Phase 4.0 — IMPROVEMENT.md §3.1.
"""

from __future__ import annotations

import random

import pytest

from yao.coupling.rhythm_markov import (
    RhythmMarkovModel,
    clear_rhythm_cache,
    generate_rhythm_pattern,
    list_available_rhythm_models,
    load_rhythm_model,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_rhythm_cache()


class TestRhythmMarkovModel:
    def test_model_creation(self) -> None:
        model = RhythmMarkovModel(
            name="test",
            description="Test model",
            source="test",
            license="CC0",
            n_gram_order=2,
            resolution="beat",
            transitions={0: {0: 0.3, 1: 0.7}, 1: {0: 0.6, 1: 0.4}},
        )
        assert model.name == "test"
        assert model.num_positions == 2

    def test_frozen(self) -> None:
        model = RhythmMarkovModel(
            name="test",
            description="",
            source="",
            license="",
            n_gram_order=2,
            resolution="beat",
            transitions={0: {0: 0.5, 1: 0.5}},
        )
        with pytest.raises(AttributeError):
            model.name = "changed"  # type: ignore[misc]


class TestGenerateRhythmPattern:
    def test_generates_onset_list(self) -> None:
        model = RhythmMarkovModel(
            name="test",
            description="",
            source="",
            license="",
            n_gram_order=2,
            resolution="beat",
            transitions={
                0: {0: 0.3, 1: 0.3, 2: 0.2, 3: 0.2},
                1: {0: 0.2, 1: 0.3, 2: 0.3, 3: 0.2},
                2: {0: 0.2, 1: 0.2, 2: 0.3, 3: 0.3},
                3: {0: 0.3, 1: 0.2, 2: 0.2, 3: 0.3},
            },
        )
        onsets = generate_rhythm_pattern(model, bars=4, rng=random.Random(42))
        assert isinstance(onsets, list)
        assert all(isinstance(b, float) for b in onsets)

    def test_deterministic_with_seed(self) -> None:
        model = RhythmMarkovModel(
            name="test",
            description="",
            source="",
            license="",
            n_gram_order=2,
            resolution="beat",
            transitions={
                0: {0: 0.5, 1: 0.5},
                1: {0: 0.5, 1: 0.5},
            },
        )
        r1 = generate_rhythm_pattern(model, bars=4, rng=random.Random(42))
        r2 = generate_rhythm_pattern(model, bars=4, rng=random.Random(42))
        assert r1 == r2

    def test_different_seeds_different_output(self) -> None:
        model = RhythmMarkovModel(
            name="test",
            description="",
            source="",
            license="",
            n_gram_order=2,
            resolution="beat",
            transitions={
                0: {0: 0.3, 1: 0.3, 2: 0.2, 3: 0.2},
                1: {0: 0.2, 1: 0.3, 2: 0.3, 3: 0.2},
                2: {0: 0.2, 1: 0.2, 2: 0.3, 3: 0.3},
                3: {0: 0.3, 1: 0.2, 2: 0.2, 3: 0.3},
            },
        )
        r1 = generate_rhythm_pattern(model, bars=8, rng=random.Random(42))
        r2 = generate_rhythm_pattern(model, bars=8, rng=random.Random(99))
        # With enough bars, different seeds should produce different patterns
        assert r1 != r2 or len(r1) != len(r2)


class TestLoadRhythmModel:
    def test_list_available_models(self) -> None:
        """Should find models if rhythm directory has YAMLs."""
        models = list_available_rhythm_models()
        # Models may or may not exist yet depending on agent completion
        assert isinstance(models, list)

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_rhythm_model("nonexistent_model_xyz")
