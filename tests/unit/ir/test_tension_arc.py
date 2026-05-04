"""Tests for TensionArc IR (Layer 3.5).

Tests cover:
- TensionArc creation and validation
- Serialization round-trip
- ArcLocation span calculation
- Integration with HarmonyPlan
"""

from __future__ import annotations

import pytest

from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.tension_arc import (
    ArcLocation,
    ArcRelease,
    TensionArc,
    TensionPattern,
)


class TestArcLocation:
    """Tests for ArcLocation."""

    def test_span(self) -> None:
        loc = ArcLocation(section="verse", bar_start=5, bar_end=8)
        assert loc.span() == 4

    def test_round_trip(self) -> None:
        loc = ArcLocation(section="chorus", bar_start=1, bar_end=4)
        data = loc.to_dict()
        restored = ArcLocation.from_dict(data)
        assert restored == loc


class TestArcRelease:
    """Tests for ArcRelease."""

    def test_round_trip(self) -> None:
        release = ArcRelease(section="chorus", bar=1)
        data = release.to_dict()
        restored = ArcRelease.from_dict(data)
        assert restored == release


class TestTensionArc:
    """Tests for TensionArc."""

    def _make_arc(self, **kwargs: object) -> TensionArc:
        defaults = {
            "id": "test_arc",
            "location": ArcLocation(section="verse", bar_start=5, bar_end=8),
            "pattern": TensionPattern.LINEAR_RISE,
            "target_release": ArcRelease(section="chorus", bar=1),
            "intensity": 0.8,
            "mechanism": "secondary_dominant_chain",
        }
        defaults.update(kwargs)
        return TensionArc(**defaults)  # type: ignore[arg-type]

    def test_creation(self) -> None:
        arc = self._make_arc()
        assert arc.id == "test_arc"
        assert arc.intensity == 0.8
        assert arc.is_resolved()

    def test_unresolved(self) -> None:
        arc = self._make_arc(target_release=None)
        assert not arc.is_resolved()

    def test_intensity_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="Intensity must be in"):
            self._make_arc(intensity=1.5)

    def test_intensity_negative(self) -> None:
        with pytest.raises(ValueError, match="Intensity must be in"):
            self._make_arc(intensity=-0.1)

    def test_span_too_short(self) -> None:
        with pytest.raises(ValueError, match="span must be 2–8"):
            self._make_arc(location=ArcLocation(section="verse", bar_start=1, bar_end=1))

    def test_span_too_long(self) -> None:
        with pytest.raises(ValueError, match="span must be 2–8"):
            self._make_arc(location=ArcLocation(section="verse", bar_start=1, bar_end=10))

    def test_round_trip(self) -> None:
        arc = self._make_arc()
        data = arc.to_dict()
        restored = TensionArc.from_dict(data)
        assert restored == arc

    def test_round_trip_no_release(self) -> None:
        arc = self._make_arc(target_release=None)
        data = arc.to_dict()
        restored = TensionArc.from_dict(data)
        assert restored == arc
        assert not restored.is_resolved()

    def test_all_patterns(self) -> None:
        for pattern in TensionPattern:
            arc = self._make_arc(pattern=pattern)
            assert arc.pattern == pattern

    def test_frozen(self) -> None:
        arc = self._make_arc()
        with pytest.raises(AttributeError):
            arc.intensity = 0.5  # type: ignore[misc]


class TestHarmonyPlanWithTensionArcs:
    """Tests for HarmonyPlan's tension_arcs field."""

    def test_default_empty(self) -> None:
        plan = HarmonyPlan()
        assert plan.tension_arcs == ()

    def test_with_arcs(self) -> None:
        arc = TensionArc(
            id="test",
            location=ArcLocation(section="verse", bar_start=1, bar_end=4),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=ArcRelease(section="chorus", bar=1),
            intensity=0.7,
        )
        plan = HarmonyPlan(tension_arcs=(arc,))
        assert len(plan.tension_arcs) == 1
        assert plan.tension_arcs[0].id == "test"

    def test_tension_arcs_in_section(self) -> None:
        arc1 = TensionArc(
            id="a1",
            location=ArcLocation(section="verse", bar_start=1, bar_end=4),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=None,
            intensity=0.5,
        )
        arc2 = TensionArc(
            id="a2",
            location=ArcLocation(section="chorus", bar_start=1, bar_end=4),
            pattern=TensionPattern.SPIKE,
            target_release=None,
            intensity=0.9,
        )
        plan = HarmonyPlan(tension_arcs=(arc1, arc2))
        assert len(plan.tension_arcs_in_section("verse")) == 1
        assert len(plan.tension_arcs_in_section("chorus")) == 1
        assert len(plan.tension_arcs_in_section("bridge")) == 0

    def test_round_trip_with_arcs(self) -> None:
        arc = TensionArc(
            id="rt",
            location=ArcLocation(section="verse", bar_start=3, bar_end=6),
            pattern=TensionPattern.DIP,
            target_release=ArcRelease(section="verse", bar=6),
            intensity=0.4,
            mechanism="modal_interchange",
        )
        plan = HarmonyPlan(tension_arcs=(arc,))
        data = plan.to_dict()
        restored = HarmonyPlan.from_dict(data)
        assert len(restored.tension_arcs) == 1
        assert restored.tension_arcs[0] == arc
