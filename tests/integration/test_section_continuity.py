"""Integration tests for section boundary continuity and motif-driven fill.

Verifies:
- Melody pitch does not reset to middle C at each section boundary
- Motif interval shape influences fill passages (thematic coherence)
"""

from __future__ import annotations

from yao.generators.note.stochastic_v2 import StochasticNoteRealizerV2
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


def _build_plan_with_motifs() -> MusicalPlan:
    """Build a 3-section plan with motif seeds and placements."""
    form = SongFormPlan(
        sections=[
            SectionPlan(
                id="verse1",
                start_bar=0,
                bars=4,
                role="verse",
                target_density=0.5,
                target_tension=0.4,
            ),
            SectionPlan(
                id="chorus",
                start_bar=4,
                bars=4,
                role="chorus",
                target_density=0.7,
                target_tension=0.8,
                is_climax=True,
            ),
            SectionPlan(
                id="verse2",
                start_bar=8,
                bars=4,
                role="verse",
                target_density=0.5,
                target_tension=0.4,
            ),
        ],
        climax_section_id="chorus",
    )

    # Ascending motif: C-D-E-F pattern (intervals 0, 2, 4, 5)
    motif_plan = MotifPlan(
        seeds=[
            MotifSeed(
                id="M1",
                rhythm_shape=(1.0, 1.0, 1.0, 1.0),
                interval_shape=(0, 2, 4, 5),
                origin_section="verse1",
                character="ascending theme",
            ),
        ],
        placements=[
            MotifPlacement(motif_id="M1", section_id="verse1", start_beat=0.0),
            MotifPlacement(motif_id="M1", section_id="chorus", start_beat=16.0),
            MotifPlacement(motif_id="M1", section_id="verse2", start_beat=32.0),
        ],
    )

    harmony = HarmonyPlan(
        chord_events=[
            ChordEvent(
                section_id="verse1",
                start_beat=0.0,
                duration_beats=16.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.3,
            ),
            ChordEvent(
                section_id="chorus",
                start_beat=16.0,
                duration_beats=16.0,
                roman="IV",
                function=HarmonicFunction.SUBDOMINANT,
                tension_level=0.7,
            ),
            ChordEvent(
                section_id="verse2",
                start_beat=32.0,
                duration_beats=16.0,
                roman="I",
                function=HarmonicFunction.TONIC,
                tension_level=0.3,
            ),
        ],
        cadences={},
        modulations=[],
    )

    return MusicalPlan(
        form=form,
        harmony=harmony,
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="Section continuity test", keywords=["test"]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            instruments=(("piano", "melody"),),
        ),
        motif=motif_plan,
    )


class TestSectionContinuity:
    """Section boundary should not cause pitch resets."""

    def test_last_pitch_carries_across_sections(self) -> None:
        """Verify the ending pitch of one section is near the starting
        pitch of the next — no reset to middle C at boundaries."""
        plan = _build_plan_with_motifs()
        realizer = StochasticNoteRealizerV2()
        prov = ProvenanceLog()
        score = realizer.realize(plan, seed=42, temperature=0.3, provenance=prov)

        assert len(score.sections) == 3

        for i in range(len(score.sections) - 1):
            sec_a = score.sections[i]
            sec_b = score.sections[i + 1]
            if not sec_a.parts[0].notes or not sec_b.parts[0].notes:
                continue
            last_note_a = max(sec_a.parts[0].notes, key=lambda n: n.start_beat)
            first_note_b = min(sec_b.parts[0].notes, key=lambda n: n.start_beat)
            gap = abs(last_note_a.pitch - first_note_b.pitch)
            assert gap <= 12, (
                f"Section boundary {sec_a.name}→{sec_b.name}: pitch gap {gap} "
                f"semitones (last={last_note_a.pitch}, first={first_note_b.pitch}). "
                f"Expected <= 12 (one octave) for smooth continuity."
            )


class TestMotifDrivenFill:
    """Fill passages should be influenced by motif interval shape."""

    def test_fill_notes_biased_toward_motif_intervals(self) -> None:
        """Fill notes should show interval distribution closer to motif
        intervals than pure random walk."""
        plan = _build_plan_with_motifs()
        realizer = StochasticNoteRealizerV2()
        prov = ProvenanceLog()
        score = realizer.realize(plan, seed=42, temperature=0.3, provenance=prov)

        # Collect all intervals between consecutive notes
        all_notes = []
        for section in score.sections:
            for part in section.parts:
                all_notes.extend(sorted(part.notes, key=lambda n: n.start_beat))
        all_notes.sort(key=lambda n: n.start_beat)

        if len(all_notes) < 2:
            return

        intervals = [all_notes[i + 1].pitch - all_notes[i].pitch for i in range(len(all_notes) - 1)]

        # Motif intervals are (0, 2, 4, 5) — mostly small ascending steps
        # The fill should have a meaningful proportion of small intervals (<=5)
        small_intervals = sum(1 for iv in intervals if abs(iv) <= 5)
        ratio = small_intervals / len(intervals)
        assert ratio >= 0.5, (
            f"Only {ratio:.0%} of intervals are small (<=5 semitones). "
            f"Motif-driven fill should produce mostly stepwise motion."
        )
