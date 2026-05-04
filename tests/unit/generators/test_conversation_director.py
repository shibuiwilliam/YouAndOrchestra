"""Tests for the Conversation Director (Step 5.5)."""

from __future__ import annotations

from yao.generators.plan.conversation_director import generate_conversation_plan
from yao.ir.conversation import ConversationPlan
from yao.ir.plan.arrangement import ArrangementPlan, InstrumentAssignment, InstrumentRole
from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.conversation import ConversationEventSpec, ConversationSpec, VoiceFocusSpec
from yao.schema.intent import IntentSpec


def _make_plan(
    with_arrangement: bool = False,
) -> MusicalPlan:
    """Create a minimal MusicalPlan for testing."""
    from yao.ir.plan.song_form import SectionPlan

    form = SongFormPlan(
        sections=[
            SectionPlan(id="intro", start_bar=0, bars=4, role="intro", target_density=0.3, target_tension=0.2),
            SectionPlan(id="verse", start_bar=4, bars=8, role="verse", target_density=0.5, target_tension=0.4),
            SectionPlan(id="chorus", start_bar=12, bars=8, role="chorus", target_density=0.8, target_tension=0.8),
        ],
        climax_section_id="chorus",
    )

    arrangement = None
    if with_arrangement:
        arrangement = ArrangementPlan(
            assignments=[
                InstrumentAssignment(instrument="piano", section_id="verse", role=InstrumentRole.MELODY),
                InstrumentAssignment(instrument="strings", section_id="verse", role=InstrumentRole.HARMONY),
                InstrumentAssignment(instrument="strings", section_id="chorus", role=InstrumentRole.MELODY),
                InstrumentAssignment(instrument="piano", section_id="chorus", role=InstrumentRole.HARMONY),
            ]
        )

    return MusicalPlan(
        form=form,
        harmony=HarmonyPlan(chord_events=[]),
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test piece", keywords=["test"]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(
            instruments=(("piano", "melody"), ("strings", "harmony"), ("bass", "bass")),
        ),
        arrangement=arrangement,
    )


class TestConversationDirectorFromSpec:
    def test_generates_plan_from_spec(self) -> None:
        plan = _make_plan()
        spec = ConversationSpec(
            voice_focus=[
                VoiceFocusSpec(section_id="verse", primary="piano", accompaniment=["strings", "bass"]),
                VoiceFocusSpec(section_id="chorus", primary="strings", accompaniment=["piano", "bass"]),
            ],
            events=[
                ConversationEventSpec(
                    type="call_response",
                    initiator="piano",
                    responder="strings",
                    section_id="verse",
                    start_bar=0,
                    end_bar=4,
                ),
            ],
        )
        result, prov = generate_conversation_plan(plan, spec)
        assert isinstance(result, ConversationPlan)
        assert result.primary_voice_for_section("verse") == "piano"
        assert result.primary_voice_for_section("chorus") == "strings"
        assert len(result.events) == 1
        assert result.events[0].type == "call_response"

    def test_provenance_recorded(self) -> None:
        plan = _make_plan()
        spec = ConversationSpec(
            voice_focus=[VoiceFocusSpec(section_id="verse", primary="piano")],
        )
        _, prov = generate_conversation_plan(plan, spec)
        assert len(prov.records) >= 1
        assert any("conversation" in r.operation for r in prov.records)


class TestConversationDirectorInferred:
    def test_infers_from_arrangement(self) -> None:
        plan = _make_plan(with_arrangement=True)
        result, prov = generate_conversation_plan(plan)
        assert isinstance(result, ConversationPlan)
        # Piano has MELODY role in verse
        assert result.primary_voice_for_section("verse") == "piano"
        # Strings has MELODY role in chorus
        assert result.primary_voice_for_section("chorus") == "strings"

    def test_infers_fallback_without_arrangement(self) -> None:
        plan = _make_plan(with_arrangement=False)
        result, _ = generate_conversation_plan(plan)
        # Fallback: first instrument as primary everywhere
        assert result.primary_voice_for_section("intro") == "piano"
        assert result.primary_voice_for_section("verse") == "piano"

    def test_does_not_produce_note_changes(self) -> None:
        """Conversation Director ONLY produces ConversationPlan, never notes."""
        plan = _make_plan(with_arrangement=True)
        result, _ = generate_conversation_plan(plan)
        # Result is a ConversationPlan, not ScoreIR or notes
        assert isinstance(result, ConversationPlan)
        # No notes exist in ConversationPlan
        assert not hasattr(result, "notes")

    def test_different_seeds_produce_same_structural_plan(self) -> None:
        """Plan structure is deterministic from spec, not seed-dependent."""
        plan = _make_plan(with_arrangement=True)
        r1, _ = generate_conversation_plan(plan, seed=1)
        r2, _ = generate_conversation_plan(plan, seed=99)
        # Without a spec, inferred plans are deterministic
        assert r1.primary_voice_per_section == r2.primary_voice_per_section
