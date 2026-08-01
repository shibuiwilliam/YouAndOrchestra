"""Regression tests for three bugs fixed together:

1. Genre placed under `generation:` was silently dropped (data fix in YAML) —
   here we assert the drum safety net correctly reads the top-level genre.
2. `_needs_drum_safety_net` must match dot- AND underscore-notation genres and
   suppress drums for the whole `classical.*` primary genre.
3. `counter_melody` instruments must render as a single sparse part (the v2
   realizer), not be double-rendered by the conductor's counter-melody path,
   and not be treated as a dense second melody.
"""

from __future__ import annotations

import collections

from yao.conductor.conductor import Conductor
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.schema.composition_v2 import InstrumentArrangementSpec


def _spec(genre: str) -> CompositionSpec:
    return CompositionSpec(
        title="Q",
        genre=genre,
        key="D minor",
        tempo_bpm=90.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="A", bars=4, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.5),
    )


class TestDrumSafetyNetGenre:
    def test_classical_dot_and_underscore_suppress_drums(self) -> None:
        cond = Conductor()
        for genre in ("classical.romantic", "classical_romantic", "classical.baroque", "classical_baroque"):
            assert cond._needs_drum_safety_net(_spec(genre)) is False, genre

    def test_classical_subgenre_prefix_suppresses_drums(self) -> None:
        # Any classical.* / classical_* primary → no drums, even if not listed.
        cond = Conductor()
        assert cond._needs_drum_safety_net(_spec("classical.impressionist")) is False
        assert cond._needs_drum_safety_net(_spec("classical_serialist")) is False

    def test_non_classical_still_gets_drums(self) -> None:
        cond = Conductor()
        assert cond._needs_drum_safety_net(_spec("pop_mainstream")) is True


class TestCompositionSpecV2CounterMelodyRole:
    def test_counter_melody_is_a_valid_role(self) -> None:
        # Fix #3a: the v2 arrangement schema accepts counter_melody (so the
        # legacy adapter no longer has to remap it to melody).
        spec = InstrumentArrangementSpec(role="counter_melody")
        assert spec.role == "counter_melody"


class TestCounterMelodyNoDoubleRender:
    def _run(self, tmp_path):
        import os

        prev = os.getcwd()
        os.chdir(tmp_path)
        try:
            spec = CompositionSpec(
                title="CM",
                genre="classical.romantic",
                key="D minor",
                tempo_bpm=90.0,
                time_signature="4/4",
                instruments=[
                    InstrumentSpec(name="violin_1", role="melody"),
                    InstrumentSpec(name="viola", role="counter_melody", counter_to="violin_1"),
                    InstrumentSpec(name="cello", role="bass"),
                ],
                sections=[SectionSpec(name="A", bars=8, dynamics="mf"), SectionSpec(name="B", bars=8, dynamics="mf")],
                generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.5),
            )
            return Conductor().compose_from_spec(spec=spec, project_name="cm", max_iterations=1)
        finally:
            os.chdir(prev)

    def test_counter_melody_single_part_and_sparser_than_melody(self, tmp_path) -> None:
        result = self._run(tmp_path)
        section = result.score.sections[0]
        counts = collections.Counter(p.instrument for p in section.parts)
        # No double-render: exactly one viola part.
        assert counts["viola"] == 1
        viola = sum(len(p.notes) for p in section.parts if p.instrument == "viola")
        melody = sum(len(p.notes) for p in section.parts if p.instrument == "violin_1")
        assert viola > 0
        # counter_melody is sparse — fewer notes than the lead melody.
        assert viola < melody
