"""Tests for Layer M1: MotifDevelopmentPlanner."""

from __future__ import annotations

import pytest

from yao.generators.melody.motif_developer import MotifDevelopmentPlanner
from yao.ir.phrase import CadenceType, PhraseFunction
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.melodic_profile import load_melodic_profile

TIER_1_GENRES = ["bebop_jazz", "j_pop_ballad", "classical_romantic", "lofi_hiphop", "rock_classic"]


def _make_spec(
    *,
    sections: list[tuple[str, int]] | None = None,
    genre: str = "general",
    seed: int = 42,
) -> CompositionSpec:
    """Create a minimal CompositionSpec for testing."""
    if sections is None:
        sections = [("verse", 8), ("chorus", 8)]
    return CompositionSpec(
        title="Test",
        genre=genre,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name=n, bars=b) for n, b in sections],
        generation=GenerationConfig(strategy="phrase_aware", seed=seed),
    )


class TestMotifDevelopmentPlanner:
    """Tests for the M1 phrase planner."""

    def test_basic_plan(self) -> None:
        """Planner produces a valid PhrasePlan."""
        spec = _make_spec()
        profile = load_melodic_profile("bebop_jazz")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        assert plan.phrase_count > 0
        assert plan.total_bars == 16  # 8 + 8
        assert len(plan.motif_library) >= 2  # primary + secondary

    def test_phrases_cover_all_bars(self) -> None:
        """Phrases must cover exactly the total bars of the spec."""
        spec = _make_spec(sections=[("A", 8), ("B", 8), ("C", 4)])
        profile = load_melodic_profile("classical_romantic")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        # Check total coverage
        total_covered = sum(p.length_bars for p in plan.phrases)
        assert total_covered == 20

    def test_phrase_boundaries_contiguous(self) -> None:
        """Phrase start/end bars are contiguous (no gaps or overlaps)."""
        spec = _make_spec(sections=[("verse", 8)])
        profile = load_melodic_profile("rock_classic")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        for i in range(1, len(plan.phrases)):
            assert plan.phrases[i].start_bar == plan.phrases[i - 1].end_bar

    def test_first_phrase_is_statement(self) -> None:
        """First phrase should be a STATEMENT."""
        spec = _make_spec(sections=[("verse", 8)])
        profile = load_melodic_profile("j_pop_ballad")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        assert plan.phrases[0].function == PhraseFunction.STATEMENT

    def test_last_phrase_has_strong_cadence(self) -> None:
        """Last phrase should have an AUTHENTIC or PLAGAL cadence."""
        spec = _make_spec(sections=[("verse", 16)])
        profile = load_melodic_profile("classical_romantic")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        last = plan.phrases[-1]
        assert last.function == PhraseFunction.ANSWER
        assert last.cadence in (CadenceType.AUTHENTIC, CadenceType.PLAGAL)

    def test_provenance_recorded(self) -> None:
        """M1 records provenance with correct layer tag."""
        spec = _make_spec()
        profile = load_melodic_profile("bebop_jazz")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        planner.plan(spec, profile, prov)

        records = prov.records
        m1_records = [r for r in records if r.layer == "M1_phrase_plan"]
        assert len(m1_records) >= 1
        assert m1_records[0].agent == "composer-subagent"

    def test_seed_reproducibility(self) -> None:
        """Same seed produces the same plan."""
        spec = _make_spec(seed=123)
        profile = load_melodic_profile("lofi_hiphop")
        planner = MotifDevelopmentPlanner()

        plan1 = planner.plan(spec, profile, ProvenanceLog())
        plan2 = planner.plan(spec, profile, ProvenanceLog())

        assert len(plan1.phrases) == len(plan2.phrases)
        for p1, p2 in zip(plan1.phrases, plan2.phrases, strict=False):
            assert p1.start_bar == p2.start_bar
            assert p1.end_bar == p2.end_bar
            assert p1.function == p2.function

    @pytest.mark.parametrize("genre", TIER_1_GENRES)
    def test_plan_for_each_genre(self, genre: str) -> None:
        """Each Tier-1 genre produces a valid plan."""
        spec = _make_spec(genre=genre)
        profile = load_melodic_profile(genre)
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        assert plan.phrase_count > 0
        assert plan.total_bars == 16
        # Every phrase has a motif assigned
        for phrase in plan.phrases:
            assert phrase.motif_id is not None
            assert phrase.motif_transformation is not None

    def test_motif_has_notes(self) -> None:
        """Generated motifs have at least 3 notes."""
        spec = _make_spec()
        profile = load_melodic_profile("bebop_jazz")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        for motif_id, motif in plan.motif_library.items():
            assert len(motif.notes) >= 3, f"Motif '{motif_id}' has too few notes"

    def test_single_bar_section(self) -> None:
        """Planner handles a 1-bar section gracefully."""
        spec = _make_spec(sections=[("tag", 1)])
        profile = load_melodic_profile("rock_classic")
        prov = ProvenanceLog()
        planner = MotifDevelopmentPlanner()

        plan = planner.plan(spec, profile, prov)

        assert plan.phrase_count >= 1
        total = sum(p.length_bars for p in plan.phrases)
        assert total == 1
