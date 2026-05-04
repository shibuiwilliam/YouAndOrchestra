"""Tests for reactive fills generation."""

from __future__ import annotations

from yao.generators.reactive_fills import (
    FillOpportunity,
    detect_fill_opportunities,
    generate_reactive_fills,
)
from yao.ir.conversation import ConversationPlan
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score_with_gaps() -> ScoreIR:
    """Create a ScoreIR with clear gaps in the melody for fills."""
    melody_notes = (
        Note(pitch=60, start_beat=0.0, duration_beats=2.0, velocity=80, instrument="piano"),
        # Gap of 2.0 beats here (beat 2.0 to 4.0)
        Note(pitch=62, start_beat=4.0, duration_beats=2.0, velocity=80, instrument="piano"),
        # Gap of 2.0 beats here (beat 6.0 to 8.0)
        Note(pitch=64, start_beat=8.0, duration_beats=2.0, velocity=80, instrument="piano"),
    )
    accompaniment_notes = (
        Note(pitch=48, start_beat=0.0, duration_beats=4.0, velocity=60, instrument="bass"),
        Note(pitch=50, start_beat=4.0, duration_beats=4.0, velocity=60, instrument="bass"),
    )
    return ScoreIR(
        title="test",
        tempo_bpm=120,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(
                name="verse",
                start_bar=0,
                end_bar=4,
                parts=(
                    Part(instrument="piano", notes=melody_notes),
                    Part(instrument="bass", notes=accompaniment_notes),
                ),
            ),
        ),
    )


def _make_conversation() -> ConversationPlan:
    """Create a ConversationPlan with piano as primary voice."""
    return ConversationPlan(
        primary_voice_per_section={"verse": "piano"},
        accompaniment_role_per_section={"verse": ("bass",)},
    )


class TestDetectFillOpportunities:
    def test_detects_gaps(self) -> None:
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        opps = detect_fill_opportunities(score, conversation, minimum_silence_beats=1.0)
        assert len(opps) >= 2  # At least 2 gaps of 2.0 beats

    def test_respects_minimum_silence(self) -> None:
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        # With very high minimum, no opportunities
        opps = detect_fill_opportunities(score, conversation, minimum_silence_beats=10.0)
        assert len(opps) == 0

    def test_no_opportunities_without_primary(self) -> None:
        score = _make_score_with_gaps()
        # No primary voice defined
        conversation = ConversationPlan()
        opps = detect_fill_opportunities(score, conversation)
        assert len(opps) == 0

    def test_opportunity_fields(self) -> None:
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        opps = detect_fill_opportunities(score, conversation)
        assert all(isinstance(o, FillOpportunity) for o in opps)
        assert all(o.section_id == "verse" for o in opps)
        assert all(o.duration_beats >= 1.0 for o in opps)


class TestGenerateReactiveFills:
    def test_inserts_fills(self) -> None:
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        result, prov = generate_reactive_fills(score, conversation, fill_instruments=["drums"], seed=42)
        # Result should have more notes than original
        orig_notes = sum(len(p.notes) for s in score.sections for p in s.parts)
        new_notes = sum(len(p.notes) for s in result.sections for p in s.parts)
        assert new_notes > orig_notes

    def test_fills_are_short(self) -> None:
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        result, _ = generate_reactive_fills(score, conversation, fill_instruments=["drums"], seed=42)
        # Find fill notes (drums)
        for section in result.sections:
            for part in section.parts:
                if part.instrument == "drums":
                    for note in part.notes:
                        # Each fill note should be short
                        assert note.duration_beats <= 1.0

    def test_provenance_recorded(self) -> None:
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        _, prov = generate_reactive_fills(score, conversation, fill_instruments=["drums"], seed=42)
        assert len(prov.records) >= 1
        assert any("reactive_fills" in r.operation for r in prov.records)

    def test_no_fills_without_opportunities(self) -> None:
        """When melody has no gaps ≥ minimum_silence, no fills are added."""
        # Notes with only 0.5 beat gaps (below default 1.0 minimum)
        continuous_melody = (
            Note(pitch=60, start_beat=0.0, duration_beats=3.5, velocity=80, instrument="piano"),
            Note(pitch=62, start_beat=4.0, duration_beats=3.5, velocity=80, instrument="piano"),
            Note(pitch=64, start_beat=8.0, duration_beats=3.5, velocity=80, instrument="piano"),
            Note(pitch=65, start_beat=12.0, duration_beats=4.0, velocity=80, instrument="piano"),
        )
        score = ScoreIR(
            title="test",
            tempo_bpm=120,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="verse",
                    start_bar=0,
                    end_bar=4,
                    parts=(Part(instrument="piano", notes=continuous_melody),),
                ),
            ),
        )
        conversation = _make_conversation()
        result, _ = generate_reactive_fills(score, conversation, fill_instruments=["drums"], minimum_silence_beats=1.0)
        orig_notes = sum(len(p.notes) for s in score.sections for p in s.parts)
        new_notes = sum(len(p.notes) for s in result.sections for p in s.parts)
        assert new_notes == orig_notes

    def test_fill_rate_above_threshold(self) -> None:
        """At least 60% of qualifying phrase endings get fills."""
        score = _make_score_with_gaps()
        conversation = _make_conversation()
        opps = detect_fill_opportunities(score, conversation, minimum_silence_beats=1.0)
        result, prov = generate_reactive_fills(score, conversation, fill_instruments=["drums"], seed=42)
        # Check provenance for fill count
        fill_record = next(r for r in prov.records if "reactive_fills" in r.operation)
        n_fills = fill_record.parameters.get("n_fills_added", 0)
        n_opps = len(opps)
        if n_opps > 0:
            fill_rate = n_fills / n_opps
            assert fill_rate >= 0.6  # At least 60%
