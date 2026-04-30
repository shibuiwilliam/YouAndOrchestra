"""Unit tests for StochasticNoteRealizer."""

from __future__ import annotations

import yao.generators.note.rule_based as _nrb  # noqa: F401
import yao.generators.note.stochastic as _nst  # noqa: F401
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.note.base import NOTE_REALIZERS
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


def _make_plan() -> MusicalPlan:
    """Create a minimal plan for testing."""
    form = SongFormPlan(
        sections=[
            SectionPlan(
                id="main", start_bar=0, bars=8, role="verse",
                target_density=0.5, target_tension=0.5,
            ),
        ],
        climax_section_id="main",
    )
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="main", start_beat=0.0, duration_beats=32.0,
                roman="I", function=HarmonicFunction.TONIC, tension_level=0.5,
            ),
        ],
    )
    return MusicalPlan(
        form=form,
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
    )


class TestStochasticNoteRealizer:
    """Unit tests for the stochastic note realizer."""

    def test_registered(self) -> None:
        assert "stochastic" in NOTE_REALIZERS

    def test_realize_produces_notes(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["stochastic"]()
        prov = ProvenanceLog()
        score = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
        assert len(score.all_notes()) > 0

    def test_different_seeds_different_output(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["stochastic"]()
        prov1 = ProvenanceLog()
        prov2 = ProvenanceLog()
        score1 = realizer.realize(plan, seed=42, temperature=0.5, provenance=prov1)
        score2 = realizer.realize(plan, seed=99, temperature=0.5, provenance=prov2)
        pitches1 = [n.pitch for n in score1.all_notes()]
        pitches2 = [n.pitch for n in score2.all_notes()]
        # Different seeds should produce at least some different pitches
        assert pitches1 != pitches2

    def test_realize_records_provenance(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["stochastic"]()
        prov = ProvenanceLog()
        realizer.realize(plan, seed=42, temperature=0.5, provenance=prov)
        assert len(prov.records) > 0

    def test_temperature_affects_output(self) -> None:
        plan = _make_plan()
        realizer = NOTE_REALIZERS["stochastic"]()
        prov_low = ProvenanceLog()
        prov_high = ProvenanceLog()
        score_low = realizer.realize(plan, seed=42, temperature=0.1, provenance=prov_low)
        score_high = realizer.realize(plan, seed=42, temperature=0.9, provenance=prov_high)
        # Different temperatures with same seed produce different results
        notes_low = score_low.all_notes()
        notes_high = score_high.all_notes()
        # At minimum, note counts or pitches should differ
        pitches_low = sorted(n.pitch for n in notes_low)
        pitches_high = sorted(n.pitch for n in notes_high)
        assert pitches_low != pitches_high or len(notes_low) != len(notes_high)
