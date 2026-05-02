"""Tests for ComposerSubagent — Wave 1.1.

Verifies:
- MotifPlan.seeds is never empty (the core v3.0 contract)
- Each motif is placed >= 3 times
- Provenance records identity_strength breakdown
- PhrasePlan covers all sections
- Empty input still produces valid seeds
"""

from __future__ import annotations

from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import CompositionSpec, GenerationConfig, InstrumentSpec, SectionSpec
from yao.schema.intent import IntentSpec
from yao.subagents.base import AgentContext
from yao.subagents.composer import ComposerSubagent


def _make_context(
    *,
    intent_text: str = "A calm piano piece",
    keywords: list[str] | None = None,
    sections: list[SectionPlan] | None = None,
    total_bars: int = 32,
) -> AgentContext:
    """Build a minimal AgentContext for Composer tests."""
    if keywords is None:
        keywords = ["calm", "piano"]

    spec = CompositionSpec(
        title="Test",
        key="C major",
        tempo_bpm=120.0,
        time_signature="4/4",
        total_bars=total_bars,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=total_bars, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=42),
    )

    intent = IntentSpec(text=intent_text, keywords=keywords)
    trajectory = MultiDimensionalTrajectory.default()

    if sections is None:
        sections = [
            SectionPlan(id="intro", start_bar=0, bars=4, role="intro", target_density=0.3, target_tension=0.2),
            SectionPlan(id="verse", start_bar=4, bars=8, role="verse", target_density=0.5, target_tension=0.4),
            SectionPlan(
                id="chorus", start_bar=12, bars=8, role="chorus", target_density=0.7, target_tension=0.8, is_climax=True
            ),
            SectionPlan(id="outro", start_bar=20, bars=4, role="outro", target_density=0.3, target_tension=0.2),
        ]

    form = SongFormPlan(sections=sections, climax_section_id="chorus")

    return AgentContext(
        spec=spec,
        intent=intent,
        trajectory=trajectory,
        form_plan=form,
    )


class TestComposerSubagent:
    """Tests for the Composer Subagent."""

    def test_motif_seeds_never_empty(self) -> None:
        """Core v3.0 contract: MotifPlan.seeds must have >= 1 element."""
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        assert output.motif_plan is not None
        assert len(output.motif_plan.seeds) >= 1

    def test_each_motif_placed_at_least_3_times(self) -> None:
        """Each seed motif must appear >= 3 times (MotifRecurrenceDetector threshold)."""
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        plan = output.motif_plan
        assert plan is not None

        for seed in plan.seeds:
            count = plan.recurrence_count(seed.id)
            assert count >= 3, f"Motif {seed.id} only placed {count} times (need >= 3)"

    def test_motif_seeds_have_valid_rhythm(self) -> None:
        """Each seed must have non-empty rhythm_shape with positive durations."""
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        for seed in output.motif_plan.seeds:
            assert len(seed.rhythm_shape) >= 2, f"Motif {seed.id} rhythm too short"
            assert all(d > 0 for d in seed.rhythm_shape), f"Motif {seed.id} has zero/negative duration"

    def test_motif_seeds_have_valid_intervals(self) -> None:
        """Each seed must have interval_shape matching rhythm_shape length."""
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        for seed in output.motif_plan.seeds:
            assert len(seed.interval_shape) == len(seed.rhythm_shape), (
                f"Motif {seed.id}: interval_shape len ({len(seed.interval_shape)}) "
                f"!= rhythm_shape len ({len(seed.rhythm_shape)})"
            )

    def test_phrase_plan_covers_all_sections(self) -> None:
        """PhrasePlan must have phrases in every section."""
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        phrase_plan = output.phrase_plan
        assert phrase_plan is not None
        assert len(phrase_plan.phrases) > 0

        section_ids = {s.id for s in context.form_plan.sections}
        covered_ids = {p.section_id for p in phrase_plan.phrases}
        assert section_ids == covered_ids, f"Uncovered sections: {section_ids - covered_ids}"

    def test_provenance_records_identity_strength(self) -> None:
        """Provenance must include identity_strength for each motif."""
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        placement_records = [r for r in output.provenance.records if r.operation == "motif_placement"]

        assert len(placement_records) >= 1
        for record in placement_records:
            assert "identity_strength" in record.parameters
            strength = record.parameters["identity_strength"]
            assert 0.0 <= strength <= 1.0

    def test_deterministic_with_same_seed(self) -> None:
        """Same input produces same output (reproducibility)."""
        context = _make_context()
        composer = ComposerSubagent()

        output1 = composer.process(context)
        output2 = composer.process(context)

        seeds1 = [(s.id, s.rhythm_shape, s.interval_shape) for s in output1.motif_plan.seeds]
        seeds2 = [(s.id, s.rhythm_shape, s.interval_shape) for s in output2.motif_plan.seeds]
        assert seeds1 == seeds2

    def test_empty_intent_still_produces_seeds(self) -> None:
        """Even with empty intent text, seeds must be produced."""
        context = _make_context(intent_text="", keywords=[])
        composer = ComposerSubagent()
        output = composer.process(context)

        assert len(output.motif_plan.seeds) >= 1

    def test_single_section_produces_seeds(self) -> None:
        """Even with a single section, seeds must be produced and placed >= 3 times."""
        sections = [
            SectionPlan(id="verse", start_bar=0, bars=8, role="verse", target_density=0.5, target_tension=0.5),
        ]
        context = _make_context(sections=sections, total_bars=8)
        composer = ComposerSubagent()
        output = composer.process(context)

        assert len(output.motif_plan.seeds) >= 1
        for seed in output.motif_plan.seeds:
            assert output.motif_plan.recurrence_count(seed.id) >= 3

    def test_many_sections_produces_multiple_motifs(self) -> None:
        """Complex forms (>= 5 sections) should produce >= 2 motifs."""
        sections = [
            SectionPlan(id="intro", start_bar=0, bars=4, role="intro", target_density=0.3, target_tension=0.2),
            SectionPlan(id="verse_a", start_bar=4, bars=8, role="verse", target_density=0.5, target_tension=0.4),
            SectionPlan(
                id="chorus", start_bar=12, bars=8, role="chorus", target_density=0.7, target_tension=0.8, is_climax=True
            ),
            SectionPlan(id="verse_b", start_bar=20, bars=8, role="verse", target_density=0.5, target_tension=0.5),
            SectionPlan(id="bridge", start_bar=28, bars=8, role="bridge", target_density=0.6, target_tension=0.6),
            SectionPlan(id="chorus_2", start_bar=36, bars=8, role="chorus", target_density=0.8, target_tension=0.9),
            SectionPlan(id="outro", start_bar=44, bars=4, role="outro", target_density=0.3, target_tension=0.2),
        ]
        context = _make_context(sections=sections, total_bars=48)
        composer = ComposerSubagent()
        output = composer.process(context)

        assert len(output.motif_plan.seeds) >= 2

    def test_different_keywords_produce_different_motifs(self) -> None:
        """Different intent keywords should affect motif character."""
        ctx_calm = _make_context(keywords=["calm", "peaceful"])
        ctx_epic = _make_context(keywords=["epic", "dramatic"])

        composer = ComposerSubagent()
        calm_output = composer.process(ctx_calm)
        epic_output = composer.process(ctx_epic)

        # Characters should differ
        calm_chars = [s.character for s in calm_output.motif_plan.seeds]
        epic_chars = [s.character for s in epic_output.motif_plan.seeds]
        assert calm_chars != epic_chars
