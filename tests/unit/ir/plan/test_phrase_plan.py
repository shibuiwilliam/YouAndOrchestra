"""Tests for PhrasePlan IR type."""

from __future__ import annotations

from yao.ir.plan.phrase import (
    Phrase,
    PhraseCadence,
    PhraseContour,
    PhrasePlan,
    PhraseRole,
)


class TestPhrase:
    """Test Phrase creation and serialization."""

    def test_create_phrase(self) -> None:
        phrase = Phrase(
            id="p1",
            section_id="verse",
            start_beat=0.0,
            length_beats=16.0,
            role=PhraseRole.ANTECEDENT,
            contour=PhraseContour.ARCH,
            cadence=PhraseCadence.HALF,
            peak_position=0.6,
        )
        assert phrase.end_beat() == 16.0
        assert phrase.role == PhraseRole.ANTECEDENT

    def test_roundtrip_dict(self) -> None:
        phrase = Phrase(
            id="p2",
            section_id="chorus",
            start_beat=16.0,
            length_beats=8.0,
            role=PhraseRole.CONSEQUENT,
            contour=PhraseContour.RISE,
            cadence=PhraseCadence.AUTHENTIC,
        )
        data = phrase.to_dict()
        restored = Phrase.from_dict(data)
        assert restored.id == phrase.id
        assert restored.role == PhraseRole.CONSEQUENT
        assert restored.cadence == PhraseCadence.AUTHENTIC


class TestPhrasePlan:
    """Test PhrasePlan queries."""

    def _make_plan(self) -> PhrasePlan:
        return PhrasePlan(
            phrases=[
                Phrase("p1", "verse", 0.0, 16.0, PhraseRole.ANTECEDENT),
                Phrase("p2", "verse", 16.0, 16.0, PhraseRole.CONSEQUENT),
                Phrase("p3", "chorus", 32.0, 16.0, PhraseRole.STAND_ALONE),
            ],
            bars_per_phrase=4.0,
            pattern="AAB",
        )

    def test_phrases_in_section(self) -> None:
        plan = self._make_plan()
        verse = plan.phrases_in_section("verse")
        assert len(verse) == 2
        chorus = plan.phrases_in_section("chorus")
        assert len(chorus) == 1

    def test_phrase_at_beat(self) -> None:
        plan = self._make_plan()
        assert plan.phrase_at_beat(8.0).id == "p1"
        assert plan.phrase_at_beat(20.0).id == "p2"
        assert plan.phrase_at_beat(40.0).id == "p3"
        assert plan.phrase_at_beat(100.0) is None

    def test_roundtrip_dict(self) -> None:
        plan = self._make_plan()
        data = plan.to_dict()
        restored = PhrasePlan.from_dict(data)
        assert len(restored.phrases) == 3
        assert restored.bars_per_phrase == 4.0
        assert restored.pattern == "AAB"
