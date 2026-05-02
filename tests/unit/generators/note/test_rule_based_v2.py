"""Tests for RuleBasedNoteRealizerV2 — Wave 1.4.

Verifies that the V2 realizer:
- Consumes MusicalPlan directly (no _plan_to_v1_spec)
- Produces valid ScoreIR with notes
- Respects chord events, motif placements, and phrase contours
- Records provenance with V2-specific metadata
"""

from __future__ import annotations

import pytest

from yao.generators.note.rule_based_v2 import RuleBasedNoteRealizerV2
from yao.ir.plan.harmony import (
    CadenceRole,
    ChordEvent,
    HarmonicFunction,
    HarmonyPlan,
)
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed, MotifTransform
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.phrase import Phrase, PhraseContour, PhrasePlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.score_ir import ScoreIR
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


@pytest.fixture()
def simple_plan() -> MusicalPlan:
    """Create a minimal but complete MusicalPlan for testing."""
    form = SongFormPlan(
        sections=[
            SectionPlan(id="verse", start_bar=0, bars=4, role="verse", target_density=0.5, target_tension=0.4),
            SectionPlan(
                id="chorus", start_bar=4, bars=4, role="chorus", target_density=0.8, target_tension=0.8, is_climax=True
            ),
        ],
        climax_section_id="chorus",
    )

    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="verse",
                start_beat=0.0,
                duration_beats=4.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.3,
            ),
            ChordEvent(
                section_id="verse",
                start_beat=4.0,
                duration_beats=4.0,
                roman="V",
                function=HarmonicFunction.DOMINANT,
                tension_level=0.5,
            ),
            ChordEvent(
                section_id="verse",
                start_beat=8.0,
                duration_beats=4.0,
                roman="vi",
                function=HarmonicFunction.TONIC,
                tension_level=0.4,
            ),
            ChordEvent(
                section_id="verse",
                start_beat=12.0,
                duration_beats=4.0,
                roman="IV",
                function=HarmonicFunction.SUBDOMINANT,
                tension_level=0.3,
                cadence_role=CadenceRole.HALF,
            ),
            ChordEvent(
                section_id="chorus",
                start_beat=16.0,
                duration_beats=4.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.7,
            ),
            ChordEvent(
                section_id="chorus",
                start_beat=20.0,
                duration_beats=4.0,
                roman="V",
                function=HarmonicFunction.DOMINANT,
                tension_level=0.9,
            ),
            ChordEvent(
                section_id="chorus",
                start_beat=24.0,
                duration_beats=4.0,
                roman="vi",
                function=HarmonicFunction.TONIC,
                tension_level=0.8,
            ),
            ChordEvent(
                section_id="chorus",
                start_beat=28.0,
                duration_beats=4.0,
                roman="IV",
                function=HarmonicFunction.SUBDOMINANT,
                tension_level=0.6,
                cadence_role=CadenceRole.AUTHENTIC,
            ),
        ],
        cadences={"verse": "half", "chorus": "authentic"},
    )

    motif = MotifPlan(
        seeds=[
            MotifSeed(
                id="M1",
                rhythm_shape=(1.0, 0.5, 0.5, 1.0),
                interval_shape=(0, 2, 4, 5),
                origin_section="verse",
                character="ascending stepwise",
            ),
        ],
        placements=[
            MotifPlacement(motif_id="M1", section_id="verse", start_beat=0.0),
            MotifPlacement(motif_id="M1", section_id="chorus", start_beat=16.0, transform=MotifTransform.SEQUENCE_UP),
            MotifPlacement(motif_id="M1", section_id="chorus", start_beat=24.0, transform=MotifTransform.INVERSION),
        ],
    )

    phrase = PhrasePlan(
        phrases=[
            Phrase(id="p1", section_id="verse", start_beat=0.0, length_beats=8.0, contour=PhraseContour.ARCH),
            Phrase(id="p2", section_id="verse", start_beat=8.0, length_beats=8.0, contour=PhraseContour.FALL),
            Phrase(id="p3", section_id="chorus", start_beat=16.0, length_beats=16.0, contour=PhraseContour.RISE),
        ],
        bars_per_phrase=4.0,
        pattern="AABA",
    )

    return MusicalPlan(
        form=form,
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="uplifting pop song", keywords=["uplifting", "pop"]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            genre="pop",
            instruments=(("piano", "melody"),),
        ),
        motif=motif,
        phrase=phrase,
    )


class TestRuleBasedNoteRealizerV2:
    """Tests for the V2 realizer."""

    def test_produces_valid_score_ir(self, simple_plan: MusicalPlan) -> None:
        """V2 realizer must produce a valid ScoreIR."""
        realizer = RuleBasedNoteRealizerV2()
        provenance = ProvenanceLog()
        score = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=provenance)

        assert isinstance(score, ScoreIR)
        assert score.key == "C major"
        assert score.tempo_bpm == 120.0
        assert len(score.sections) == 2

    def test_produces_notes(self, simple_plan: MusicalPlan) -> None:
        """V2 realizer must produce actual notes (not empty)."""
        realizer = RuleBasedNoteRealizerV2()
        provenance = ProvenanceLog()
        score = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=provenance)

        all_notes = score.all_notes()
        assert len(all_notes) > 0

    def test_respects_section_structure(self, simple_plan: MusicalPlan) -> None:
        """Each section in the score must correspond to the plan's sections."""
        realizer = RuleBasedNoteRealizerV2()
        provenance = ProvenanceLog()
        score = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=provenance)

        assert score.sections[0].name == "verse"
        assert score.sections[0].start_bar == 0
        assert score.sections[0].end_bar == 4
        assert score.sections[1].name == "chorus"
        assert score.sections[1].start_bar == 4
        assert score.sections[1].end_bar == 8

    def test_chorus_higher_velocity_than_verse(self, simple_plan: MusicalPlan) -> None:
        """Chorus (higher tension) should have higher average velocity."""
        realizer = RuleBasedNoteRealizerV2()
        provenance = ProvenanceLog()
        score = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=provenance)

        verse_notes = list(score.sections[0].parts[0].notes)
        chorus_notes = list(score.sections[1].parts[0].notes)

        if verse_notes and chorus_notes:
            verse_avg_vel = sum(n.velocity for n in verse_notes) / len(verse_notes)
            chorus_avg_vel = sum(n.velocity for n in chorus_notes) / len(chorus_notes)
            assert chorus_avg_vel > verse_avg_vel

    def test_motif_placement_creates_notes(self, simple_plan: MusicalPlan) -> None:
        """Motif placements must produce notes at their designated positions."""
        realizer = RuleBasedNoteRealizerV2()
        provenance = ProvenanceLog()
        score = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=provenance)

        # The first motif placement is at beat 0.0 in verse
        verse_notes = list(score.sections[0].parts[0].notes)
        # Should have notes starting at beat 0.0 (the motif)
        start_beats = [n.start_beat for n in verse_notes]
        assert 0.0 in start_beats

    def test_records_v2_provenance(self, simple_plan: MusicalPlan) -> None:
        """Provenance must indicate V2 realizer with consumed fields."""
        realizer = RuleBasedNoteRealizerV2()
        provenance = ProvenanceLog()
        realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=provenance)

        records = provenance.records
        v2_records = [r for r in records if r.operation == "note_realization_v2"]
        assert len(v2_records) == 1
        assert v2_records[0].parameters["realizer"] == "rule_based_v2"
        assert "consumed_fields" in v2_records[0].parameters

    def test_no_plan_to_v1_spec_call(self) -> None:
        """V2 must not call _plan_to_v1_spec in any function body."""
        import ast
        import inspect

        import yao.generators.note.rule_based_v2 as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        # Check that no function/method calls _plan_to_v1_spec
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "_plan_to_v1_spec":
                    pytest.fail("V2 realizer calls _plan_to_v1_spec")
                if isinstance(node.func, ast.Attribute) and node.func.attr == "_plan_to_v1_spec":
                    pytest.fail("V2 realizer calls _plan_to_v1_spec")

    def test_no_legacy_adapter_import(self) -> None:
        """V2 must not import from legacy_adapter."""
        import ast
        import inspect

        import yao.generators.note.rule_based_v2 as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "legacy_adapter" in node.module:
                pytest.fail("V2 realizer imports from legacy_adapter")

    def test_consumed_plan_fields_declared(self) -> None:
        """V2 must declare consumed_plan_fields."""
        realizer = RuleBasedNoteRealizerV2()
        assert len(realizer.consumed_plan_fields) >= 7

    def test_deterministic_with_same_seed(self, simple_plan: MusicalPlan) -> None:
        """Same seed must produce identical output."""
        realizer = RuleBasedNoteRealizerV2()
        score1 = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=ProvenanceLog())
        score2 = realizer.realize(simple_plan, seed=42, temperature=0.0, provenance=ProvenanceLog())

        notes1 = score1.all_notes()
        notes2 = score2.all_notes()
        assert len(notes1) == len(notes2)
        for n1, n2 in zip(notes1, notes2, strict=False):
            assert n1.pitch == n2.pitch
            assert n1.start_beat == n2.start_beat

    def test_handles_plan_without_motifs(self, simple_plan: MusicalPlan) -> None:
        """V2 must work even when motif plan is None."""
        # Create plan without motifs
        plan_no_motif = MusicalPlan(
            form=simple_plan.form,
            harmony=simple_plan.harmony,
            trajectory=simple_plan.trajectory,
            intent=simple_plan.intent,
            provenance=ProvenanceLog(),
            global_context=simple_plan.global_context,
            motif=None,
            phrase=None,
        )
        realizer = RuleBasedNoteRealizerV2()
        score = realizer.realize(plan_no_motif, seed=42, temperature=0.0, provenance=ProvenanceLog())
        assert len(score.all_notes()) > 0
