"""Tests for SongFormPlan."""

from __future__ import annotations

import pytest

from yao.ir.plan.song_form import SectionPlan, SongFormPlan


def _make_sections() -> list[SectionPlan]:
    """Create a standard 3-section form for testing."""
    return [
        SectionPlan(
            id="intro", start_bar=0, bars=4, role="intro",
            target_density=0.2, target_tension=0.1,
        ),
        SectionPlan(
            id="verse", start_bar=4, bars=8, role="verse",
            target_density=0.5, target_tension=0.4,
        ),
        SectionPlan(
            id="chorus", start_bar=12, bars=8, role="chorus",
            target_density=0.9, target_tension=0.8, is_climax=True,
        ),
    ]


class TestSectionPlan:
    """SectionPlan construction and serialization."""

    def test_end_bar(self) -> None:
        s = SectionPlan(
            id="verse", start_bar=4, bars=8, role="verse",
            target_density=0.5, target_tension=0.4,
        )
        assert s.end_bar() == 12

    def test_round_trip(self) -> None:
        s = SectionPlan(
            id="chorus", start_bar=12, bars=8, role="chorus",
            target_density=0.9, target_tension=0.8, is_climax=True,
        )
        d = s.to_dict()
        s2 = SectionPlan.from_dict(d)
        assert s2.id == "chorus"
        assert s2.start_bar == 12
        assert s2.bars == 8
        assert s2.is_climax is True
        assert s2.target_density == 0.9

    def test_frozen(self) -> None:
        s = SectionPlan(
            id="intro", start_bar=0, bars=4, role="intro",
            target_density=0.2, target_tension=0.1,
        )
        with pytest.raises(AttributeError):
            s.bars = 8  # type: ignore[misc]


class TestSongFormPlan:
    """SongFormPlan construction, queries, and serialization."""

    def test_total_bars(self) -> None:
        plan = SongFormPlan(sections=_make_sections(), climax_section_id="chorus")
        assert plan.total_bars() == 20  # 4 + 8 + 8

    def test_section_at_bar(self) -> None:
        plan = SongFormPlan(sections=_make_sections(), climax_section_id="chorus")
        assert plan.section_at_bar(0) is not None
        assert plan.section_at_bar(0).id == "intro"  # type: ignore[union-attr]
        assert plan.section_at_bar(3).id == "intro"  # type: ignore[union-attr]
        assert plan.section_at_bar(4).id == "verse"  # type: ignore[union-attr]
        assert plan.section_at_bar(11).id == "verse"  # type: ignore[union-attr]
        assert plan.section_at_bar(12).id == "chorus"  # type: ignore[union-attr]
        assert plan.section_at_bar(19).id == "chorus"  # type: ignore[union-attr]
        assert plan.section_at_bar(20) is None  # out of range

    def test_section_by_id(self) -> None:
        plan = SongFormPlan(sections=_make_sections(), climax_section_id="chorus")
        assert plan.section_by_id("verse") is not None
        assert plan.section_by_id("verse").bars == 8  # type: ignore[union-attr]
        assert plan.section_by_id("nonexistent") is None

    def test_section_ids(self) -> None:
        plan = SongFormPlan(sections=_make_sections(), climax_section_id="chorus")
        assert plan.section_ids() == ["intro", "verse", "chorus"]

    def test_round_trip(self) -> None:
        plan = SongFormPlan(sections=_make_sections(), climax_section_id="chorus")
        d = plan.to_dict()
        plan2 = SongFormPlan.from_dict(d)
        assert plan2.total_bars() == 20
        assert plan2.climax_section_id == "chorus"
        assert len(plan2.sections) == 3
        assert plan2.sections[2].is_climax is True

    def test_empty_plan(self) -> None:
        plan = SongFormPlan()
        assert plan.total_bars() == 0
        assert plan.section_at_bar(0) is None
