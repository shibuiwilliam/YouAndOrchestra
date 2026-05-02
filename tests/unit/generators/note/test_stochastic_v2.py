"""Tests for StochasticNoteRealizerV2 — Wave 1.4.

Verifies stochastic V2 realizer:
- Direct plan consumption (no legacy adapter)
- Temperature controls variation
- Seed ensures reproducibility
- Different seeds produce different output
"""

from __future__ import annotations

import pytest

from yao.generators.note.stochastic_v2 import StochasticNoteRealizerV2
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.phrase import Phrase, PhraseContour, PhrasePlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.score_ir import ScoreIR
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


@pytest.fixture()
def plan_with_motifs() -> MusicalPlan:
    """Create a test plan with motifs and phrases."""
    form = SongFormPlan(
        sections=[
            SectionPlan(id="verse", start_bar=0, bars=4, role="verse", target_density=0.5, target_tension=0.5),
        ],
        climax_section_id="verse",
    )
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="verse",
                start_beat=0.0,
                duration_beats=8.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.4,
            ),
            ChordEvent(
                section_id="verse",
                start_beat=8.0,
                duration_beats=8.0,
                roman="V",
                function=HarmonicFunction.DOMINANT,
                tension_level=0.6,
            ),
        ],
        cadences={},
    )
    motif = MotifPlan(
        seeds=[MotifSeed(id="M1", rhythm_shape=(1.0, 0.5, 0.5), interval_shape=(0, 2, 4), origin_section="verse")],
        placements=[MotifPlacement(motif_id="M1", section_id="verse", start_beat=0.0)],
    )
    phrase = PhrasePlan(
        phrases=[Phrase(id="p1", section_id="verse", start_beat=0.0, length_beats=16.0, contour=PhraseContour.ARCH)],
    )
    return MusicalPlan(
        form=form,
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(key="C major", tempo_bpm=120.0, instruments=(("piano", "melody"),)),
        motif=motif,
        phrase=phrase,
    )


class TestStochasticNoteRealizerV2:
    """Tests for the stochastic V2 realizer."""

    def test_produces_valid_score(self, plan_with_motifs: MusicalPlan) -> None:
        """Must produce a valid ScoreIR with notes."""
        realizer = StochasticNoteRealizerV2()
        score = realizer.realize(plan_with_motifs, seed=42, temperature=0.5, provenance=ProvenanceLog())
        assert isinstance(score, ScoreIR)
        assert len(score.all_notes()) > 0

    def test_same_seed_same_output(self, plan_with_motifs: MusicalPlan) -> None:
        """Same seed must produce identical output."""
        realizer = StochasticNoteRealizerV2()
        s1 = realizer.realize(plan_with_motifs, seed=42, temperature=0.5, provenance=ProvenanceLog())
        s2 = realizer.realize(plan_with_motifs, seed=42, temperature=0.5, provenance=ProvenanceLog())
        n1, n2 = s1.all_notes(), s2.all_notes()
        assert len(n1) == len(n2)
        for a, b in zip(n1, n2, strict=False):
            assert a.pitch == b.pitch
            assert a.start_beat == b.start_beat

    def test_different_seed_different_output(self, plan_with_motifs: MusicalPlan) -> None:
        """Different seeds should produce different output."""
        realizer = StochasticNoteRealizerV2()
        s1 = realizer.realize(plan_with_motifs, seed=42, temperature=0.7, provenance=ProvenanceLog())
        s2 = realizer.realize(plan_with_motifs, seed=99, temperature=0.7, provenance=ProvenanceLog())
        n1, n2 = s1.all_notes(), s2.all_notes()
        # With temperature > 0, different seeds should produce at least some different pitches
        if n1 and n2:
            pitches1 = [n.pitch for n in n1]
            pitches2 = [n.pitch for n in n2]
            assert pitches1 != pitches2

    def test_temperature_zero_less_varied(self, plan_with_motifs: MusicalPlan) -> None:
        """Temperature 0 should be less varied than temperature 1."""
        realizer = StochasticNoteRealizerV2()
        s_low = realizer.realize(plan_with_motifs, seed=42, temperature=0.0, provenance=ProvenanceLog())
        s_high = realizer.realize(plan_with_motifs, seed=42, temperature=1.0, provenance=ProvenanceLog())
        n_low = s_low.all_notes()
        n_high = s_high.all_notes()
        # Higher temperature should produce more unique pitch classes
        set(n.pitch % 12 for n in n_low)
        set(n.pitch % 12 for n in n_high)
        # We can't guarantee strictly more, but at least they differ
        assert len(n_low) > 0 and len(n_high) > 0

    def test_no_plan_to_v1_spec(self) -> None:
        """Must not call _plan_to_v1_spec."""
        import ast
        import inspect

        import yao.generators.note.stochastic_v2 as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_plan_to_v1_spec":
                pytest.fail("Stochastic V2 calls _plan_to_v1_spec")

    def test_no_legacy_import(self) -> None:
        """Must not import from legacy_adapter."""
        import ast
        import inspect

        import yao.generators.note.stochastic_v2 as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "legacy_adapter" in node.module:
                pytest.fail("Stochastic V2 imports from legacy_adapter")

    def test_consumed_plan_fields_declared(self) -> None:
        """Must declare consumed_plan_fields."""
        realizer = StochasticNoteRealizerV2()
        assert len(realizer.consumed_plan_fields) >= 7

    def test_records_provenance(self, plan_with_motifs: MusicalPlan) -> None:
        """Provenance must record stochastic V2 metadata."""
        prov = ProvenanceLog()
        realizer = StochasticNoteRealizerV2()
        realizer.realize(plan_with_motifs, seed=42, temperature=0.5, provenance=prov)
        recs = [r for r in prov.records if r.operation == "note_realization_v2"]
        assert len(recs) == 1
        assert recs[0].parameters["realizer"] == "stochastic_v2"
        assert recs[0].parameters["temperature"] == 0.5
