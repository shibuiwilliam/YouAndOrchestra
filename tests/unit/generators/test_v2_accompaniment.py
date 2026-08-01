"""The v2 realizers must render full arrangements, not melody-only (P1.1 prereq).

Regression guard: ``stochastic_v2`` / ``rule_based_v2`` previously emitted a
single melody ``Part`` per section, which made them non-viable as a default
(flipping would drop all accompaniment). They now render harmony/bass parts
from the plan's chord events.
"""

from __future__ import annotations

import pytest

from yao.generators.legacy_adapter import build_plan_from_v1
from yao.generators.note.accompaniment import realize_accompaniment_for_role
from yao.generators.note.base import NOTE_REALIZERS
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec


def _multi_instrument_spec() -> CompositionSpec:
    return CompositionSpec(
        title="Arrangement",
        key="F major",
        tempo_bpm=120.0,
        time_signature="4/4",
        instruments=[
            InstrumentSpec(name="piano", role="melody"),
            InstrumentSpec(name="strings", role="harmony"),
            InstrumentSpec(name="contrabass", role="bass"),
        ],
        sections=[
            SectionSpec(name="A", bars=4, dynamics="mf"),
            SectionSpec(name="B", bars=4, dynamics="mf"),
        ],
        # The v1 spec strategy must be a base strategy accepted by the v2
        # pipeline schema; the v2 realizer under test is chosen directly below.
        generation=GenerationConfig(strategy="stochastic", seed=5, temperature=0.5),
    )


@pytest.mark.parametrize("realizer_name", ["stochastic_v2", "rule_based_v2"])
def test_v2_realizer_emits_all_instruments(realizer_name: str) -> None:
    spec = _multi_instrument_spec()
    plan, prov = build_plan_from_v1(spec)
    realizer = NOTE_REALIZERS[realizer_name]()
    score = realizer.realize(plan, seed=5, temperature=0.5, provenance=prov, original_spec=spec)

    for section in score.sections:
        instruments_with_notes = {p.instrument for p in section.parts if p.notes}
        # Every spec instrument should be present and sounding.
        assert "piano" in instruments_with_notes, f"{realizer_name}: melody missing in {section.name}"
        assert "strings" in instruments_with_notes, f"{realizer_name}: harmony missing in {section.name}"
        assert "contrabass" in instruments_with_notes, f"{realizer_name}: bass missing in {section.name}"


@pytest.mark.parametrize("realizer_name", ["stochastic_v2", "rule_based_v2"])
def test_v2_bass_is_below_melody(realizer_name: str) -> None:
    spec = _multi_instrument_spec()
    plan, prov = build_plan_from_v1(spec)
    realizer = NOTE_REALIZERS[realizer_name]()
    score = realizer.realize(plan, seed=5, temperature=0.5, provenance=prov, original_spec=spec)

    bass_pitches = [n.pitch for s in score.sections for p in s.parts if p.instrument == "contrabass" for n in p.notes]
    melody_pitches = [n.pitch for s in score.sections for p in s.parts if p.instrument == "piano" for n in p.notes]
    assert bass_pitches, "bass should sound"
    assert melody_pitches, "melody should sound"
    # Bass register sits clearly below the melodic register.
    assert max(bass_pitches) < sum(melody_pitches) / len(melody_pitches)


class TestAccompanimentUnit:
    def _chords(self) -> list[ChordEvent]:
        return [
            ChordEvent("A", 0.0, 4.0, "I", HarmonicFunction.TONIC, 0.3),
            ChordEvent("A", 4.0, 4.0, "V", HarmonicFunction.DOMINANT, 0.6),
        ]

    def test_sparse_bass_pulses_per_bar(self) -> None:
        # Sparse density → one root per bar.
        notes = realize_accompaniment_for_role(
            "bass", "bass", self._chords(), "F", "major", base_velocity=90, beats_per_bar=4.0, density=0.2
        )
        # 2 chords x 4 beats each / 4-beat pulse = 2 bass notes.
        assert len(notes) == 2
        assert all(n.instrument == "bass" for n in notes)

    def test_sparse_harmony_is_sustained_block_chords(self) -> None:
        # Sparse density → one sustained voicing per chord.
        notes = realize_accompaniment_for_role(
            "harmony", "pad", self._chords(), "F", "major", base_velocity=90, beats_per_bar=4.0, density=0.2
        )
        # Multiple voices per chord, sustained for the chord duration.
        assert len(notes) >= 4
        assert all(n.duration_beats == 4.0 for n in notes)

    def test_no_chords_no_notes(self) -> None:
        assert realize_accompaniment_for_role("harmony", "pad", [], "F", "major", 90, 4.0) == []


class TestDensityAwareAccompaniment:
    """Accompaniment busyness scales with section density (P1.4 / contrast)."""

    def _chords(self, bars: int = 2) -> list[ChordEvent]:
        return [
            ChordEvent("A", float(i) * 4, 4.0, r, HarmonicFunction.TONIC, 0.4)
            for i, r in enumerate((["I", "V"] * bars)[:bars])
        ]

    def test_bass_denser_sections_have_more_notes(self) -> None:
        chords = self._chords(2)
        sparse = realize_accompaniment_for_role("bass", "bass", chords, "F", "major", 90, 4.0, density=0.2)
        busy = realize_accompaniment_for_role("bass", "bass", chords, "F", "major", 90, 4.0, density=0.9)
        assert len(busy) > len(sparse)

    def test_harmony_denser_sections_have_more_notes(self) -> None:
        chords = self._chords(2)
        sparse = realize_accompaniment_for_role("harmony", "pad", chords, "F", "major", 90, 4.0, density=0.2)
        busy = realize_accompaniment_for_role("harmony", "pad", chords, "F", "major", 90, 4.0, density=0.9)
        assert len(busy) > len(sparse)

    def test_sparse_bass_is_one_per_bar(self) -> None:
        chords = self._chords(2)  # two 4-beat chords = 2 bars in 4/4
        sparse = realize_accompaniment_for_role("bass", "bass", chords, "F", "major", 90, 4.0, density=0.2)
        assert len(sparse) == 2
