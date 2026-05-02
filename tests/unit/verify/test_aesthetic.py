"""Tests for aesthetic evaluation metrics — Wave 2.2.

Tests each of the 4 metrics individually plus the aggregate.
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec
from yao.verify.aesthetic import (
    AestheticReport,
    compute_contrast_index,
    compute_memorability_index,
    compute_pacing_index,
    compute_surprise_index,
    evaluate_aesthetics,
)


def _make_plan(
    key: str = "C major",
    sections: list[SectionPlan] | None = None,
    motif: MotifPlan | None = None,
) -> MusicalPlan:
    """Helper to build a MusicalPlan for testing."""
    if sections is None:
        sections = [
            SectionPlan(id="verse", start_bar=0, bars=4, role="verse", target_density=0.5, target_tension=0.5),
            SectionPlan(id="chorus", start_bar=4, bars=4, role="chorus", target_density=0.8, target_tension=0.8),
        ]
    form = SongFormPlan(sections=sections, climax_section_id="chorus")
    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id=s.id,
                start_beat=s.start_bar * 4.0,
                duration_beats=s.bars * 4.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=s.target_tension,
            )
            for s in sections
        ],
        cadences={},
    )
    return MusicalPlan(
        form=form,
        harmony=harmony,
        motif=motif,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(key=key, tempo_bpm=120.0),
    )


def _make_score_monotone(n_notes: int = 32) -> ScoreIR:
    """Create a boring monotone score (same pitch, same velocity)."""
    notes = tuple(
        Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=64, instrument="piano") for i in range(n_notes)
    )
    return ScoreIR(
        title="Monotone",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=notes[:16]),)),
            Section(name="chorus", start_bar=4, end_bar=8, parts=(Part(instrument="piano", notes=notes[16:]),)),
        ),
    )


def _make_score_varied() -> ScoreIR:
    """Create a musically varied score (different pitches, velocities per section)."""
    verse_notes = tuple(
        Note(pitch=60 + (i % 7), start_beat=float(i), duration_beats=1.0, velocity=50 + (i % 3) * 5, instrument="piano")
        for i in range(16)
    )
    chorus_notes = tuple(
        Note(
            pitch=72 + (i % 5),
            start_beat=16.0 + float(i * 0.5),
            duration_beats=0.5,
            velocity=90 + (i % 4) * 5,
            instrument="piano",
        )
        for i in range(24)
    )
    return ScoreIR(
        title="Varied",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=verse_notes),)),
            Section(name="chorus", start_bar=4, end_bar=8, parts=(Part(instrument="piano", notes=chorus_notes),)),
        ),
    )


class TestSurpriseIndex:
    """Tests for compute_surprise_index."""

    def test_returns_float_in_range(self) -> None:
        plan = _make_plan()
        score = _make_score_monotone()
        result = compute_surprise_index(score, plan)
        assert 0.0 <= result <= 1.0

    def test_monotone_is_high_surprise(self) -> None:
        """Repeating the same note is SURPRISING in bigram model (self-transition is rare)."""
        plan = _make_plan()
        score = _make_score_monotone()
        result = compute_surprise_index(score, plan)
        # Self-transition has low probability (0.05) → high surprise
        assert result > 0.5

    def test_stepwise_is_low_surprise(self) -> None:
        """Stepwise motion (scale run) is the EXPECTED pattern in bigram model."""
        plan = _make_plan()
        # C major scale ascending: C D E F G A B C (degrees 0,1,2,3,4,5,6,0)
        notes = tuple(
            Note(
                pitch=60 + [0, 2, 4, 5, 7, 9, 11, 12][i % 8],
                start_beat=float(i),
                duration_beats=1.0,
                velocity=64,
                instrument="piano",
            )
            for i in range(16)
        )
        score = ScoreIR(
            title="Stepwise",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=notes),)),
                Section(name="chorus", start_bar=4, end_bar=8, parts=(Part(instrument="piano", notes=notes),)),
            ),
        )
        result = compute_surprise_index(score, plan)
        # Stepwise motion has higher probability → lower surprise
        monotone_surprise = compute_surprise_index(_make_score_monotone(), plan)
        assert result < monotone_surprise

    def test_empty_score(self) -> None:
        plan = _make_plan()
        empty = ScoreIR(title="Empty", tempo_bpm=120.0, time_signature="4/4", key="C major", sections=())
        assert compute_surprise_index(empty, plan) == 0.0


class TestMemorabilityIndex:
    """Tests for compute_memorability_index."""

    def test_no_motifs_is_zero(self) -> None:
        plan = _make_plan(motif=None)
        assert compute_memorability_index(plan) == 0.0

    def test_empty_seeds_is_zero(self) -> None:
        plan = _make_plan(motif=MotifPlan(seeds=[], placements=[]))
        assert compute_memorability_index(plan) == 0.0

    def test_recurring_motif_scores_higher(self) -> None:
        """A motif with 4+ placements should score well."""
        motif = MotifPlan(
            seeds=[MotifSeed(id="M1", rhythm_shape=(1.0, 0.5), interval_shape=(0, 5), origin_section="verse")],
            placements=[
                MotifPlacement(motif_id="M1", section_id="verse", start_beat=0.0),
                MotifPlacement(motif_id="M1", section_id="verse", start_beat=4.0),
                MotifPlacement(motif_id="M1", section_id="chorus", start_beat=16.0),
                MotifPlacement(motif_id="M1", section_id="chorus", start_beat=20.0),
            ],
        )
        plan = _make_plan(motif=motif)
        result = compute_memorability_index(plan)
        assert result > 0.3

    def test_single_placement_scores_lower(self) -> None:
        """A motif with only 1 placement should score poorly."""
        motif = MotifPlan(
            seeds=[MotifSeed(id="M1", rhythm_shape=(1.0,), interval_shape=(0,), origin_section="verse")],
            placements=[MotifPlacement(motif_id="M1", section_id="verse", start_beat=0.0)],
        )
        plan = _make_plan(motif=motif)
        result = compute_memorability_index(plan)
        assert result < 0.4


class TestContrastIndex:
    """Tests for compute_contrast_index."""

    def test_returns_float_in_range(self) -> None:
        score = _make_score_varied()
        result = compute_contrast_index(score)
        assert 0.0 <= result <= 1.0

    def test_monotone_has_low_contrast(self) -> None:
        """Identical sections should have near-zero contrast."""
        score = _make_score_monotone()
        result = compute_contrast_index(score)
        assert result < 0.1

    def test_varied_has_higher_contrast(self) -> None:
        """Different sections should have measurable contrast."""
        score = _make_score_varied()
        result = compute_contrast_index(score)
        assert result > 0.1

    def test_single_section_is_zero(self) -> None:
        notes = tuple(
            Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=64, instrument="piano") for i in range(8)
        )
        score = ScoreIR(
            title="Single",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(Section(name="only", start_bar=0, end_bar=2, parts=(Part(instrument="piano", notes=notes),)),),
        )
        assert compute_contrast_index(score) == 0.0


class TestPacingIndex:
    """Tests for compute_pacing_index."""

    def test_returns_float_in_range(self) -> None:
        plan = _make_plan()
        score = _make_score_varied()
        result = compute_pacing_index(score, plan)
        assert 0.0 <= result <= 1.0

    def test_matching_velocity_arc(self) -> None:
        """When velocity matches target tension, pacing should be high."""
        plan = _make_plan(
            sections=[
                SectionPlan(id="verse", start_bar=0, bars=4, role="verse", target_density=0.5, target_tension=0.3),
                SectionPlan(id="chorus", start_bar=4, bars=4, role="chorus", target_density=0.8, target_tension=0.8),
            ]
        )
        # Create score where velocity matches: verse=low, chorus=high
        verse_notes = tuple(
            Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=55, instrument="piano") for i in range(16)
        )
        chorus_notes = tuple(
            Note(pitch=72, start_beat=16.0 + float(i), duration_beats=1.0, velocity=105, instrument="piano")
            for i in range(16)
        )
        score = ScoreIR(
            title="Matched",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=verse_notes),)),
                Section(name="chorus", start_bar=4, end_bar=8, parts=(Part(instrument="piano", notes=chorus_notes),)),
            ),
        )
        result = compute_pacing_index(score, plan)
        assert result >= 0.6

    def test_mismatched_velocity_arc(self) -> None:
        """When velocity is opposite to tension, pacing should be low."""
        plan = _make_plan(
            sections=[
                SectionPlan(id="verse", start_bar=0, bars=4, role="verse", target_density=0.5, target_tension=0.8),
                SectionPlan(id="chorus", start_bar=4, bars=4, role="chorus", target_density=0.8, target_tension=0.2),
            ]
        )
        # Verse velocity high, chorus velocity low → matches plan target
        # But let's invert: verse=low vel (mismatches 0.8 tension), chorus=high vel (mismatches 0.2 tension)
        verse_notes = tuple(
            Note(pitch=60, start_beat=float(i), duration_beats=1.0, velocity=40, instrument="piano") for i in range(16)
        )
        chorus_notes = tuple(
            Note(pitch=72, start_beat=16.0 + float(i), duration_beats=1.0, velocity=120, instrument="piano")
            for i in range(16)
        )
        score = ScoreIR(
            title="Mismatched",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=verse_notes),)),
                Section(name="chorus", start_bar=4, end_bar=8, parts=(Part(instrument="piano", notes=chorus_notes),)),
            ),
        )
        result = compute_pacing_index(score, plan)
        assert result < 0.5


class TestEvaluateAesthetics:
    """Tests for the aggregate function."""

    def test_returns_aesthetic_report(self) -> None:
        plan = _make_plan()
        score = _make_score_varied()
        report = evaluate_aesthetics(score, plan)
        assert isinstance(report, AestheticReport)
        assert 0.0 <= report.aggregate <= 1.0

    def test_monotone_scores_lower_than_varied(self) -> None:
        plan = _make_plan(
            motif=MotifPlan(
                seeds=[MotifSeed(id="M1", rhythm_shape=(1.0, 0.5), interval_shape=(0, 4), origin_section="verse")],
                placements=[
                    MotifPlacement(motif_id="M1", section_id="verse", start_beat=0.0),
                    MotifPlacement(motif_id="M1", section_id="chorus", start_beat=16.0),
                    MotifPlacement(motif_id="M1", section_id="chorus", start_beat=20.0),
                ],
            )
        )
        monotone = evaluate_aesthetics(_make_score_monotone(), plan)
        varied = evaluate_aesthetics(_make_score_varied(), plan)
        # Varied should at least have higher contrast
        assert varied.contrast > monotone.contrast
