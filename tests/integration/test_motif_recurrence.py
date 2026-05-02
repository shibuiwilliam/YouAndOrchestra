"""Integration tests for motif recurrence — Wave 1.1.

Verifies the full Composer → Critic pipeline:
- Composer generates non-empty MotifPlan
- MotifRecurrenceDetector evaluates motif placements (not silent)
- MotifAbsenceDetector does NOT fire when seeds are present

These tests close Gap-1 and Gap-8 from docs/audit/2026-05-status-reaudit.md.
"""

from __future__ import annotations

from yao.ir.plan.motif import MotifPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.intent import IntentSpec
from yao.subagents.base import AgentContext
from yao.subagents.composer import ComposerSubagent
from yao.verify.critique.melodic import MotifRecurrenceDetector
from yao.verify.critique.memorability import MotifAbsenceDetector


def _make_context(
    *,
    intent_text: str = "An epic orchestral piece",
    keywords: list[str] | None = None,
) -> AgentContext:
    """Build a realistic AgentContext for integration tests."""
    if keywords is None:
        keywords = ["epic", "orchestral"]

    spec = CompositionSpec(
        title="Integration Test",
        key="D minor",
        tempo_bpm=110.0,
        time_signature="4/4",
        total_bars=32,
        instruments=[
            InstrumentSpec(name="strings_ensemble", role="melody"),
            InstrumentSpec(name="cello", role="bass"),
        ],
        sections=[
            SectionSpec(name="intro", bars=4, dynamics="pp"),
            SectionSpec(name="verse", bars=8, dynamics="mp"),
            SectionSpec(name="chorus", bars=8, dynamics="f"),
            SectionSpec(name="bridge", bars=4, dynamics="mf"),
            SectionSpec(name="outro", bars=8, dynamics="pp"),
        ],
        generation=GenerationConfig(strategy="stochastic", seed=42),
    )

    form = SongFormPlan(
        sections=[
            SectionPlan(id="intro", start_bar=0, bars=4, role="intro", target_density=0.3, target_tension=0.2),
            SectionPlan(id="verse", start_bar=4, bars=8, role="verse", target_density=0.5, target_tension=0.4),
            SectionPlan(
                id="chorus", start_bar=12, bars=8, role="chorus", target_density=0.7, target_tension=0.8, is_climax=True
            ),
            SectionPlan(id="bridge", start_bar=20, bars=4, role="bridge", target_density=0.5, target_tension=0.6),
            SectionPlan(id="outro", start_bar=24, bars=8, role="outro", target_density=0.3, target_tension=0.2),
        ],
        climax_section_id="chorus",
    )

    return AgentContext(
        spec=spec,
        intent=IntentSpec(text=intent_text, keywords=keywords),
        trajectory=MultiDimensionalTrajectory.default(),
        form_plan=form,
    )


def _make_v2_spec() -> CompositionSpecV2:
    """Build a minimal CompositionSpecV2 for critic tests."""
    return CompositionSpecV2.model_validate(
        {
            "version": "2",
            "identity": {"title": "Critic Test", "duration_sec": 90},
            "global": {"key": "D minor", "bpm": 110, "time_signature": "4/4"},
            "form": {
                "sections": [
                    {"id": "intro", "bars": 4, "density": 0.3},
                    {"id": "verse", "bars": 8, "density": 0.5},
                    {"id": "chorus", "bars": 8, "density": 0.7},
                    {"id": "bridge", "bars": 4, "density": 0.5},
                    {"id": "outro", "bars": 8, "density": 0.3},
                ]
            },
            "harmony": {"chord_palette": ["i", "iv", "V7", "VI"]},
            "arrangement": {"instruments": {"strings_ensemble": {"role": "melody"}}},
            "generation": {"strategy": "stochastic"},
        }
    )


class TestComposerCriticIntegration:
    """Integration: Composer → MotifPlan → Critic pipeline."""

    def test_critic_detects_recurrence_with_real_composer(self) -> None:
        """MotifRecurrenceDetector evaluates a real (non-empty) MotifPlan.

        With the Composer producing seeds and >= 3 placements, the detector
        should run its recurrence check and return no findings (all motifs
        are placed >= 3 times).
        """
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        assert output.motif_plan is not None
        assert len(output.motif_plan.seeds) >= 1

        # Build a MusicalPlan-like object with the motif plan
        from yao.ir.plan.harmony import HarmonyPlan
        from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
        from yao.reflect.provenance import ProvenanceLog

        plan = MusicalPlan(
            form=context.form_plan,
            harmony=HarmonyPlan(chord_events=[], cadences={}, modulations=[]),
            trajectory=context.trajectory,
            intent=context.intent,
            provenance=ProvenanceLog(),
            global_context=GlobalContext(key="D minor", tempo_bpm=110.0),
            motif=output.motif_plan,
            phrase=output.phrase_plan,
        )

        spec_v2 = _make_v2_spec()

        # Run MotifRecurrenceDetector
        detector = MotifRecurrenceDetector()
        findings = detector.detect(plan, spec_v2)

        # With >= 3 placements per motif, there should be NO recurrence findings
        assert len(findings) == 0, f"Unexpected recurrence findings: {[f.issue for f in findings]}"

    def test_no_silent_pass_on_non_empty_plan(self) -> None:
        """MotifAbsenceDetector should NOT fire when seeds are present.

        This verifies Gap-8: with a real Composer, the absence detector
        sees seeds and returns no findings.
        """
        context = _make_context()
        composer = ComposerSubagent()
        output = composer.process(context)

        from yao.ir.plan.harmony import HarmonyPlan
        from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
        from yao.reflect.provenance import ProvenanceLog

        plan = MusicalPlan(
            form=context.form_plan,
            harmony=HarmonyPlan(chord_events=[], cadences={}, modulations=[]),
            trajectory=context.trajectory,
            intent=context.intent,
            provenance=ProvenanceLog(),
            global_context=GlobalContext(),
            motif=output.motif_plan,
        )

        spec_v2 = _make_v2_spec()

        detector = MotifAbsenceDetector()
        findings = detector.detect(plan, spec_v2)

        # Seeds are present → no absence finding
        assert len(findings) == 0, f"MotifAbsenceDetector fired despite non-empty seeds: {[f.issue for f in findings]}"

    def test_absence_detector_fires_on_empty_plan(self) -> None:
        """MotifAbsenceDetector SHOULD fire when seeds are empty.

        This confirms the detector is not broken — it correctly identifies
        the absence of motifs.
        """
        from yao.ir.plan.harmony import HarmonyPlan
        from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
        from yao.reflect.provenance import ProvenanceLog

        form = SongFormPlan(
            sections=[
                SectionPlan(id="verse", start_bar=0, bars=8, role="verse", target_density=0.5, target_tension=0.5),
            ],
            climax_section_id="verse",
        )

        plan = MusicalPlan(
            form=form,
            harmony=HarmonyPlan(chord_events=[], cadences={}, modulations=[]),
            trajectory=MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text="test", keywords=[]),
            provenance=ProvenanceLog(),
            global_context=GlobalContext(),
            motif=MotifPlan(seeds=[], placements=[]),  # Deliberately empty
        )

        spec_v2 = _make_v2_spec()

        detector = MotifAbsenceDetector()
        findings = detector.detect(plan, spec_v2)

        assert len(findings) == 1
        assert findings[0].rule_id == "motif_absence"

    def test_recurrence_detector_catches_insufficient_placement(self) -> None:
        """MotifRecurrenceDetector flags motifs placed fewer than 3 times.

        This proves the detector is functional, not just silent-passing.
        """
        from yao.ir.plan.harmony import HarmonyPlan
        from yao.ir.plan.motif import MotifPlacement, MotifSeed
        from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
        from yao.reflect.provenance import ProvenanceLog

        form = SongFormPlan(
            sections=[
                SectionPlan(id="verse", start_bar=0, bars=8, role="verse", target_density=0.5, target_tension=0.5),
            ],
            climax_section_id="verse",
        )

        # Motif with only 1 placement (below threshold of 3)
        weak_plan = MotifPlan(
            seeds=[
                MotifSeed(
                    id="M1",
                    rhythm_shape=(1.0, 1.0, 1.0, 1.0),
                    interval_shape=(0, 2, 4, 5),
                    origin_section="verse",
                    character="test motif",
                ),
            ],
            placements=[
                MotifPlacement(motif_id="M1", section_id="verse", start_beat=0.0),
            ],
        )

        plan = MusicalPlan(
            form=form,
            harmony=HarmonyPlan(chord_events=[], cadences={}, modulations=[]),
            trajectory=MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text="test", keywords=[]),
            provenance=ProvenanceLog(),
            global_context=GlobalContext(),
            motif=weak_plan,
        )

        spec_v2 = _make_v2_spec()

        detector = MotifRecurrenceDetector()
        findings = detector.detect(plan, spec_v2)

        assert len(findings) == 1
        assert findings[0].rule_id == "melody.motif_recurrence"
        assert "only 1 time" in findings[0].issue.lower()
