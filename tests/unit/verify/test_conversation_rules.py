"""Tests for conversation critique rules."""

from __future__ import annotations

from tests.helpers import make_minimal_spec_v2
from yao.ir.conversation import ConversationPlan
from yao.ir.plan.arrangement import ArrangementPlan, InstrumentAssignment, InstrumentRole
from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec
from yao.verify.critique.conversation_rules import (
    ConversationSilenceDetector,
    FillAbsenceDetector,
    FrequencyCollisionUnresolvedDetector,
    PrimaryVoiceAmbiguityDetector,
)


def _make_plan(
    conversation: ConversationPlan | None = None,
    n_instruments: int = 3,
    with_arrangement: bool = False,
) -> MusicalPlan:
    """Create a MusicalPlan for testing."""
    instruments = (("piano", "melody"), ("strings", "harmony"), ("bass", "bass"))[:n_instruments]

    arrangement = None
    if with_arrangement:
        arrangement = ArrangementPlan(
            assignments=[
                InstrumentAssignment(
                    instrument="piano",
                    section_id="verse",
                    role=InstrumentRole.MELODY,
                    register_low=48,
                    register_high=84,
                ),
                InstrumentAssignment(
                    instrument="strings",
                    section_id="verse",
                    role=InstrumentRole.HARMONY,
                    register_low=48,
                    register_high=84,  # Same register = overlap
                ),
            ]
        )

    return MusicalPlan(
        form=SongFormPlan(
            sections=[
                SectionPlan(id="verse", start_bar=0, bars=8, role="verse", target_density=0.5, target_tension=0.4),
                SectionPlan(id="chorus", start_bar=8, bars=8, role="chorus", target_density=0.8, target_tension=0.8),
            ],
            climax_section_id="chorus",
        ),
        harmony=HarmonyPlan(chord_events=[]),
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(instruments=instruments),
        conversation=conversation,
        arrangement=arrangement,
    )


def _make_spec():
    return make_minimal_spec_v2()


class TestConversationSilence:
    def test_fires_on_multi_instrument_without_plan(self) -> None:
        plan = _make_plan(conversation=None, n_instruments=3)
        findings = ConversationSilenceDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "conversation.silence" in findings[0].rule_id

    def test_no_finding_for_single_instrument(self) -> None:
        plan = _make_plan(conversation=None, n_instruments=1)
        findings = ConversationSilenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0

    def test_no_finding_with_conversation_plan(self) -> None:
        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
            events=(
                # Having at least one event avoids the "empty events" suggestion
            ),
        )
        plan = _make_plan(conversation=conversation, n_instruments=3)
        # With plan but no events and >= 3 instruments → suggestion
        findings = ConversationSilenceDetector().detect(plan, _make_spec())
        # Should be a suggestion (not missing plan)
        if findings:
            assert findings[0].severity.value == "suggestion"


class TestPrimaryVoiceAmbiguity:
    def test_fires_when_section_has_no_primary(self) -> None:
        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
            # chorus has no primary
        )
        plan = _make_plan(conversation=conversation, n_instruments=3)
        findings = PrimaryVoiceAmbiguityDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "chorus" in findings[0].issue

    def test_no_finding_when_all_sections_have_primary(self) -> None:
        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano", "chorus": "strings"},
        )
        plan = _make_plan(conversation=conversation, n_instruments=3)
        findings = PrimaryVoiceAmbiguityDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestFillAbsence:
    def test_fires_when_no_fill_events(self) -> None:
        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
            events=(),  # No events at all
        )
        plan = _make_plan(conversation=conversation, n_instruments=3)
        findings = FillAbsenceDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "fill" in findings[0].issue.lower()

    def test_no_finding_with_fill_events(self) -> None:
        from yao.ir.conversation import BarRange, ConversationEvent

        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
            events=(
                ConversationEvent(
                    type="fill_in_response",
                    initiator="piano",
                    responder="drums",
                    location=BarRange(start=4, end=5),
                    duration_beats=4.0,
                ),
            ),
        )
        plan = _make_plan(conversation=conversation, n_instruments=3)
        findings = FillAbsenceDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestFrequencyCollisionUnresolved:
    def test_fires_on_register_overlap(self) -> None:
        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
            accompaniment_role_per_section={"verse": ("strings",)},
        )
        plan = _make_plan(
            conversation=conversation,
            n_instruments=3,
            with_arrangement=True,
        )
        findings = FrequencyCollisionUnresolvedDetector().detect(plan, _make_spec())
        assert len(findings) >= 1
        assert "overlap" in findings[0].issue.lower()

    def test_no_finding_without_arrangement(self) -> None:
        conversation = ConversationPlan(
            primary_voice_per_section={"verse": "piano"},
        )
        plan = _make_plan(conversation=conversation, n_instruments=3, with_arrangement=False)
        findings = FrequencyCollisionUnresolvedDetector().detect(plan, _make_spec())
        assert len(findings) == 0
