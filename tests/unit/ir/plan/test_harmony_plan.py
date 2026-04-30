"""Tests for HarmonyPlan."""

from __future__ import annotations

from yao.ir.plan.harmony import (
    CadenceRole,
    ChordEvent,
    HarmonicFunction,
    HarmonyPlan,
    ModulationEvent,
)


def _make_chord_events() -> list[ChordEvent]:
    """Create a standard I-V-vi-IV progression over 16 beats."""
    return [
        ChordEvent(
            section_id="verse",
            start_beat=0.0,
            duration_beats=4.0,
            roman="I",
            function=HarmonicFunction.TONIC,
            tension_level=0.2,
        ),
        ChordEvent(
            section_id="verse",
            start_beat=4.0,
            duration_beats=4.0,
            roman="V",
            function=HarmonicFunction.DOMINANT,
            tension_level=0.6,
        ),
        ChordEvent(
            section_id="verse",
            start_beat=8.0,
            duration_beats=4.0,
            roman="vi",
            function=HarmonicFunction.TONIC,
            tension_level=0.3,
        ),
        ChordEvent(
            section_id="verse",
            start_beat=12.0,
            duration_beats=4.0,
            roman="IV",
            function=HarmonicFunction.SUBDOMINANT,
            tension_level=0.4,
            cadence_role=CadenceRole.PLAGAL,
        ),
    ]


class TestChordEvent:
    """ChordEvent construction and serialization."""

    def test_end_beat(self) -> None:
        c = ChordEvent(
            section_id="verse",
            start_beat=4.0,
            duration_beats=4.0,
            roman="V",
            function=HarmonicFunction.DOMINANT,
            tension_level=0.6,
        )
        assert c.end_beat() == 8.0

    def test_round_trip(self) -> None:
        c = ChordEvent(
            section_id="chorus",
            start_beat=0.0,
            duration_beats=2.0,
            roman="V/V",
            function=HarmonicFunction.DOMINANT,
            tension_level=0.8,
            cadence_role=CadenceRole.AUTHENTIC,
        )
        d = c.to_dict()
        c2 = ChordEvent.from_dict(d)
        assert c2.roman == "V/V"
        assert c2.function == HarmonicFunction.DOMINANT
        assert c2.cadence_role == CadenceRole.AUTHENTIC

    def test_no_cadence(self) -> None:
        c = ChordEvent(
            section_id="verse",
            start_beat=0.0,
            duration_beats=4.0,
            roman="I",
            function=HarmonicFunction.TONIC,
            tension_level=0.2,
        )
        d = c.to_dict()
        assert d["cadence_role"] is None
        c2 = ChordEvent.from_dict(d)
        assert c2.cadence_role is None


class TestHarmonyPlan:
    """HarmonyPlan queries and serialization."""

    def test_chord_at_beat(self) -> None:
        plan = HarmonyPlan(chord_events=_make_chord_events())
        chord = plan.chord_at_beat(0.0)
        assert chord is not None
        assert chord.roman == "I"

        chord = plan.chord_at_beat(5.0)
        assert chord is not None
        assert chord.roman == "V"

        chord = plan.chord_at_beat(15.9)
        assert chord is not None
        assert chord.roman == "IV"

        assert plan.chord_at_beat(16.0) is None  # past end

    def test_chords_in_section(self) -> None:
        plan = HarmonyPlan(chord_events=_make_chord_events())
        verse_chords = plan.chords_in_section("verse")
        assert len(verse_chords) == 4
        assert plan.chords_in_section("chorus") == []

    def test_cadences(self) -> None:
        plan = HarmonyPlan(
            chord_events=_make_chord_events(),
            cadences={"verse": CadenceRole.HALF, "chorus": CadenceRole.AUTHENTIC},
        )
        assert plan.section_cadence("verse") == CadenceRole.HALF
        assert plan.section_cadence("chorus") == CadenceRole.AUTHENTIC
        assert plan.section_cadence("bridge") is None

    def test_modulations(self) -> None:
        mod = ModulationEvent(
            at_beat=32.0,
            from_key="C major",
            to_key="G major",
            method="pivot_chord",
        )
        plan = HarmonyPlan(modulations=[mod])
        assert len(plan.modulations) == 1
        d = mod.to_dict()
        mod2 = ModulationEvent.from_dict(d)
        assert mod2.to_key == "G major"

    def test_round_trip(self) -> None:
        plan = HarmonyPlan(
            chord_events=_make_chord_events(),
            cadences={"verse": CadenceRole.HALF},
            modulations=[
                ModulationEvent(at_beat=32.0, from_key="C major", to_key="G major"),
            ],
            tension_resolution_points=[15.0, 31.0],
        )
        d = plan.to_dict()
        plan2 = HarmonyPlan.from_dict(d)
        assert len(plan2.chord_events) == 4
        assert plan2.cadences["verse"] == CadenceRole.HALF
        assert len(plan2.modulations) == 1
        assert plan2.tension_resolution_points == [15.0, 31.0]

    def test_empty_plan(self) -> None:
        plan = HarmonyPlan()
        assert plan.chord_at_beat(0) is None
        assert plan.chords_in_section("any") == []
