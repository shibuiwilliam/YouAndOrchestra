"""Tests for ConversationPlan IR."""

from __future__ import annotations

import pytest

from yao.ir.conversation import BarRange, ConversationEvent, ConversationPlan


class TestBarRange:
    def test_creation(self) -> None:
        r = BarRange(start=0, end=4)
        assert r.length == 4

    def test_contains(self) -> None:
        r = BarRange(start=2, end=6)
        assert r.contains(2)
        assert r.contains(5)
        assert not r.contains(6)
        assert not r.contains(1)

    def test_invalid_range_raises(self) -> None:
        with pytest.raises(ValueError, match="end must be > start"):
            BarRange(start=5, end=3)

    def test_negative_start_raises(self) -> None:
        with pytest.raises(ValueError, match="start must be >= 0"):
            BarRange(start=-1, end=3)

    def test_serialization_round_trip(self) -> None:
        r = BarRange(start=4, end=8)
        assert BarRange.from_dict(r.to_dict()) == r


class TestConversationEvent:
    def test_creation(self) -> None:
        event = ConversationEvent(
            type="call_response",
            initiator="piano",
            responder="strings",
            location=BarRange(start=0, end=4),
            duration_beats=16.0,
        )
        assert event.type == "call_response"
        assert event.initiator == "piano"
        assert event.responder == "strings"

    def test_serialization_round_trip(self) -> None:
        event = ConversationEvent(
            type="trade",
            initiator="saxophone",
            responder="trumpet",
            location=BarRange(start=8, end=16),
            duration_beats=32.0,
        )
        restored = ConversationEvent.from_dict(event.to_dict())
        assert restored == event

    def test_tutti_no_responder(self) -> None:
        event = ConversationEvent(
            type="tutti",
            initiator="ensemble",
            responder=None,
            location=BarRange(start=0, end=2),
            duration_beats=8.0,
        )
        assert event.responder is None


class TestConversationPlan:
    def _make_plan(self) -> ConversationPlan:
        return ConversationPlan(
            events=(
                ConversationEvent(
                    type="call_response",
                    initiator="piano",
                    responder="strings",
                    location=BarRange(start=0, end=4),
                    duration_beats=16.0,
                ),
                ConversationEvent(
                    type="fill_in_response",
                    initiator="bass",
                    responder="drums",
                    location=BarRange(start=4, end=8),
                    duration_beats=16.0,
                ),
            ),
            primary_voice_per_section={
                "verse": "piano",
                "chorus": "strings",
            },
            accompaniment_role_per_section={
                "verse": ("strings", "bass"),
                "chorus": ("piano", "bass"),
            },
        )

    def test_events_in_bar(self) -> None:
        plan = self._make_plan()
        assert len(plan.events_in_bar(2)) == 1
        assert plan.events_in_bar(2)[0].type == "call_response"
        assert len(plan.events_in_bar(5)) == 1
        assert plan.events_in_bar(5)[0].type == "fill_in_response"
        assert len(plan.events_in_bar(10)) == 0

    def test_primary_voice_for_section(self) -> None:
        plan = self._make_plan()
        assert plan.primary_voice_for_section("verse") == "piano"
        assert plan.primary_voice_for_section("chorus") == "strings"
        assert plan.primary_voice_for_section("bridge") is None

    def test_accompaniment_for_section(self) -> None:
        plan = self._make_plan()
        assert plan.accompaniment_for_section("verse") == ("strings", "bass")
        assert plan.accompaniment_for_section("unknown") == ()

    def test_serialization_round_trip(self) -> None:
        plan = self._make_plan()
        restored = ConversationPlan.from_dict(plan.to_dict())
        assert len(restored.events) == 2
        assert restored.primary_voice_per_section == plan.primary_voice_per_section
        assert restored.accompaniment_role_per_section == plan.accompaniment_role_per_section

    def test_empty_plan(self) -> None:
        plan = ConversationPlan()
        assert len(plan.events) == 0
        assert plan.primary_voice_for_section("any") is None
