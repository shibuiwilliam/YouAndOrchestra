"""Property-based tests for genre invariants.

Verifies that generators respect key/range/section constraints
across multiple seeds and strategies.
"""

from __future__ import annotations

import pytest

import yao.generators.constraint_solver as _cs  # noqa: F401
import yao.generators.markov as _mk  # noqa: F401
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.constants.instruments import INSTRUMENT_RANGES
from yao.generators.registry import get_generator
from yao.ir.notation import parse_key, scale_notes
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec

_STRATEGIES = ["rule_based", "stochastic", "markov", "constraint_satisfaction"]
_SEEDS = [1, 42, 99, 256, 1000]


def _make_spec(strategy: str, seed: int, key: str = "C major") -> CompositionSpec:
    return CompositionSpec(
        title="Property Test",
        key=key,
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
        generation=GenerationConfig(strategy=strategy, seed=seed, temperature=0.5),
    )


class TestKeyInvariant:
    """All generators must produce notes within the specified key."""

    @pytest.mark.parametrize("strategy", _STRATEGIES)
    @pytest.mark.parametrize("seed", _SEEDS)
    def test_notes_in_key(self, strategy: str, seed: int) -> None:
        gen = get_generator(strategy)
        score, _ = gen.generate(_make_spec(strategy, seed))
        root, st = parse_key("C major")
        valid_pcs = set()
        for o in range(0, 10):
            for n in scale_notes(root, st, o):
                if 0 <= n <= 127:
                    valid_pcs.add(n % 12)
        for note in score.all_notes():
            assert note.pitch % 12 in valid_pcs, f"{strategy}/seed={seed}: note {note.pitch} not in C major"


class TestRangeInvariant:
    """All generators must produce notes within instrument range."""

    @pytest.mark.parametrize("strategy", _STRATEGIES)
    def test_piano_range(self, strategy: str) -> None:
        gen = get_generator(strategy)
        score, _ = gen.generate(_make_spec(strategy, 42))
        r = INSTRUMENT_RANGES["piano"]
        for note in score.all_notes():
            assert r.midi_low <= note.pitch <= r.midi_high


class TestSectionInvariant:
    """All generators must produce the correct number of sections."""

    @pytest.mark.parametrize("strategy", _STRATEGIES)
    def test_section_count(self, strategy: str) -> None:
        spec = _make_spec(strategy, 42)
        gen = get_generator(strategy)
        score, _ = gen.generate(spec)
        assert len(score.sections) == len(spec.sections)


class TestProvenanceInvariant:
    """All generators must produce non-empty provenance."""

    @pytest.mark.parametrize("strategy", _STRATEGIES)
    def test_provenance_nonempty(self, strategy: str) -> None:
        gen = get_generator(strategy)
        _, prov = gen.generate(_make_spec(strategy, 42))
        assert len(prov) > 0
