"""Tests for MusicalPlan."""

from __future__ import annotations

from yao.ir.plan.harmony import (
    CadenceRole,
    ChordEvent,
    HarmonicFunction,
    HarmonyPlan,
)
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


def _make_minimal_plan() -> MusicalPlan:
    """Create a minimal Phase α plan."""
    form = SongFormPlan(
        sections=[
            SectionPlan(
                id="intro", start_bar=0, bars=4, role="intro",
                target_density=0.2, target_tension=0.1,
            ),
            SectionPlan(
                id="chorus", start_bar=4, bars=8, role="chorus",
                target_density=0.9, target_tension=0.8, is_climax=True,
            ),
        ],
        climax_section_id="chorus",
    )
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="intro", start_beat=0.0, duration_beats=16.0,
                roman="I", function=HarmonicFunction.TONIC, tension_level=0.1,
            ),
            ChordEvent(
                section_id="chorus", start_beat=16.0, duration_beats=16.0,
                roman="V", function=HarmonicFunction.DOMINANT, tension_level=0.7,
                cadence_role=CadenceRole.AUTHENTIC,
            ),
        ],
        cadences={"chorus": CadenceRole.AUTHENTIC},
    )
    return MusicalPlan(
        form=form,
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="A test piece", keywords=["test"]),
        provenance=ProvenanceLog(),
    )


class TestMusicalPlan:
    """MusicalPlan integration tests."""

    def test_is_complete_false_in_phase_alpha(self) -> None:
        plan = _make_minimal_plan()
        assert not plan.is_complete()

    def test_is_phase_alpha_complete(self) -> None:
        plan = _make_minimal_plan()
        assert plan.is_phase_alpha_complete()

    def test_phase_alpha_incomplete_without_chords(self) -> None:
        plan = MusicalPlan(
            form=SongFormPlan(
                sections=[
                    SectionPlan(
                        id="intro", start_bar=0, bars=4, role="intro",
                        target_density=0.2, target_tension=0.1,
                    ),
                ],
                climax_section_id="intro",
            ),
            harmony=HarmonyPlan(),  # empty
            trajectory=MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text="test", keywords=[]),
            provenance=ProvenanceLog(),
        )
        assert not plan.is_phase_alpha_complete()

    def test_phase_beta_fields_none(self) -> None:
        plan = _make_minimal_plan()
        assert plan.motifs_phrases is None
        assert plan.arrangement is None
        assert plan.drums is None

    def test_json_round_trip(self) -> None:
        plan = _make_minimal_plan()
        json_str = plan.to_json()
        plan2 = MusicalPlan.from_json(json_str)
        assert plan2.form.total_bars() == 12
        assert len(plan2.harmony.chord_events) == 2
        assert plan2.harmony.cadences["chorus"] == CadenceRole.AUTHENTIC
        assert plan2.intent.text == "A test piece"

    def test_to_dict_structure(self) -> None:
        plan = _make_minimal_plan()
        d = plan.to_dict()
        assert "form" in d
        assert "harmony" in d
        assert "intent_text" in d
        assert "motifs_phrases" not in d  # None fields excluded
        assert "arrangement" not in d

    def test_form_access(self) -> None:
        plan = _make_minimal_plan()
        assert plan.form.total_bars() == 12
        assert plan.form.climax_section_id == "chorus"

    def test_harmony_access(self) -> None:
        plan = _make_minimal_plan()
        chord = plan.harmony.chord_at_beat(0.0)
        assert chord is not None
        assert chord.roman == "I"

    def test_trajectory_access(self) -> None:
        plan = _make_minimal_plan()
        assert plan.trajectory.value_at("tension", 0) == 0.5  # default
