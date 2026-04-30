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
                id="intro",
                start_bar=0,
                bars=4,
                role="intro",
                target_density=0.2,
                target_tension=0.1,
            ),
            SectionPlan(
                id="chorus",
                start_bar=4,
                bars=8,
                role="chorus",
                target_density=0.9,
                target_tension=0.8,
                is_climax=True,
            ),
        ],
        climax_section_id="chorus",
    )
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="intro",
                start_beat=0.0,
                duration_beats=16.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.1,
            ),
            ChordEvent(
                section_id="chorus",
                start_beat=16.0,
                duration_beats=16.0,
                roman="V",
                function=HarmonicFunction.DOMINANT,
                tension_level=0.7,
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
                        id="intro",
                        start_bar=0,
                        bars=4,
                        role="intro",
                        target_density=0.2,
                        target_tension=0.1,
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
        assert plan.motif is None
        assert plan.phrase is None
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
        assert "global_context" in d
        assert "motif" not in d  # None fields excluded
        assert "arrangement" not in d

    def test_json_round_trip_with_phase_beta_fields(self) -> None:
        """Test that Phase β fields survive JSON roundtrip."""
        from yao.ir.plan.arrangement import (
            ArrangementPlan,
            InstrumentAssignment,
            InstrumentRole,
        )
        from yao.ir.plan.drums import DrumHit, DrumPattern, KitPiece
        from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed, MotifTransform
        from yao.ir.plan.musical_plan import GlobalContext
        from yao.ir.plan.phrase import Phrase, PhraseCadence, PhrasePlan, PhraseRole

        plan = MusicalPlan(
            form=_make_minimal_plan().form,
            harmony=_make_minimal_plan().harmony,
            trajectory=MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text="Phase β test", keywords=[]),
            provenance=ProvenanceLog(),
            global_context=GlobalContext(
                key="G major",
                tempo_bpm=132.0,
                time_signature="3/4",
                instruments=(("piano", "melody"), ("cello", "bass")),
            ),
            motif=MotifPlan(
                seeds=[MotifSeed("M1", (1.0, 0.5), (0, 2), "verse", "hook")],
                placements=[
                    MotifPlacement("M1", "verse", 0.0),
                    MotifPlacement("M1", "chorus", 16.0, MotifTransform.INVERSION),
                ],
            ),
            phrase=PhrasePlan(
                phrases=[
                    Phrase("p1", "verse", 0.0, 16.0, PhraseRole.ANTECEDENT, cadence=PhraseCadence.HALF),
                ],
                bars_per_phrase=4.0,
                pattern="AB",
            ),
            arrangement=ArrangementPlan(
                assignments=[
                    InstrumentAssignment("piano", "verse", InstrumentRole.MELODY),
                ],
            ),
            drums=DrumPattern(
                id="waltz",
                genre="classical",
                time_signature="3/4",
                hits=[DrumHit(0.0, 0.25, KitPiece.KICK, 100)],
            ),
        )
        json_str = plan.to_json()
        plan2 = MusicalPlan.from_json(json_str)

        # Verify all Phase β fields survived
        assert plan2.global_context.key == "G major"
        assert plan2.global_context.tempo_bpm == 132.0
        assert len(plan2.global_context.instruments) == 2
        assert plan2.motif is not None
        assert len(plan2.motif.seeds) == 1
        assert plan2.motif.seeds[0].character == "hook"
        assert len(plan2.motif.placements) == 2
        assert plan2.phrase is not None
        assert len(plan2.phrase.phrases) == 1
        assert plan2.phrase.pattern == "AB"
        assert plan2.arrangement is not None
        assert len(plan2.arrangement.assignments) == 1
        assert plan2.drums is not None
        assert plan2.drums.id == "waltz"
        assert len(plan2.drums.hits) == 1

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
