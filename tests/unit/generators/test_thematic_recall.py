"""Tests for automatic thematic recurrence (P1.2)."""

from __future__ import annotations

import pytest

from yao.generators.thematic_recall import (
    _section_stem,
    auto_thematic_recall,
    compute_thematic_recalls,
)
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


def _spec(section_names: list[str], recalls: dict[str, str] | None = None) -> CompositionSpec:
    recalls = recalls or {}
    return CompositionSpec(
        title="Theme Test",
        key="F major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=8, dynamics="mf", recall_melody_from=recalls.get(n)) for n in section_names],
        generation=GenerationConfig(strategy="stochastic", seed=1, temperature=0.5),
    )


class TestSectionStem:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("A", "a"),
            ("A_prime", "a"),
            ("A_doublePrime", "a"),
            ("A'", "a"),
            ("A''", "a"),
            ("verse", "verse"),
            ("verse_2", "verse"),
            ("return_a", "a"),
            ("reprise_chorus", "chorus"),
            ("chorus_reprise", "chorus"),
            ("intro", "intro"),
            ("theme_a", "theme_a"),
        ],
    )
    def test_stem_normalization(self, name: str, expected: str) -> None:
        assert _section_stem(name) == expected

    def test_never_empty(self) -> None:
        # Pathological all-marker name must not normalize to empty.
        assert _section_stem("prime") != ""


class TestComputeThematicRecalls:
    def test_abaca_form(self) -> None:
        """A_prime and A_doublePrime recall A; B and C do not."""
        spec = _spec(["intro", "A", "B", "A_prime", "C", "A_doublePrime", "coda"])
        got = {a.section: a.recalls for a in compute_thematic_recalls(spec)}
        assert got == {"A_prime": "A", "A_doublePrime": "A"}

    def test_verse_chorus(self) -> None:
        spec = _spec(["verse", "chorus", "verse_2", "chorus_2"])
        got = {a.section: a.recalls for a in compute_thematic_recalls(spec)}
        assert got == {"verse_2": "verse", "chorus_2": "chorus"}

    def test_no_returns_no_assignments(self) -> None:
        spec = _spec(["intro", "verse", "bridge", "outro"])
        assert compute_thematic_recalls(spec) == []

    def test_respects_explicit_recall(self) -> None:
        """A user-set recall_melody_from is never overridden."""
        spec = _spec(["A", "A_prime"], recalls={"A_prime": "intro"})
        assert compute_thematic_recalls(spec) == []

    def test_first_occurrence_is_the_theme(self) -> None:
        spec = _spec(["A", "A_prime", "A_doublePrime"])
        for a in compute_thematic_recalls(spec):
            assert a.recalls == "A"


class TestAutoThematicRecall:
    def test_applies_recalls(self) -> None:
        spec = _spec(["A", "B", "A_prime"])
        new_spec, assignments = auto_thematic_recall(spec)
        assert len(assignments) == 1
        by_name = {s.name: s for s in new_spec.sections}
        assert by_name["A_prime"].recall_melody_from == "A"
        assert by_name["A"].recall_melody_from is None
        assert by_name["B"].recall_melody_from is None

    def test_noop_returns_original_spec(self) -> None:
        spec = _spec(["intro", "verse", "outro"])
        new_spec, assignments = auto_thematic_recall(spec)
        assert assignments == []
        assert new_spec is spec  # unchanged identity when nothing to do

    def test_does_not_mutate_input(self) -> None:
        spec = _spec(["A", "A_prime"])
        auto_thematic_recall(spec)
        # Original spec's section is untouched (immutability).
        assert spec.sections[1].recall_melody_from is None
