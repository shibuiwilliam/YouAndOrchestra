"""Tests for ArrangementPlan IR type."""

from __future__ import annotations

from yao.ir.plan.arrangement import (
    ArrangementPlan,
    InstrumentAssignment,
    InstrumentRole,
)


class TestInstrumentAssignment:
    """Test InstrumentAssignment creation and serialization."""

    def test_create_assignment(self) -> None:
        assignment = InstrumentAssignment(
            instrument="violin",
            section_id="verse",
            role=InstrumentRole.MELODY,
            register_low=55,
            register_high=96,
            articulation="legato",
        )
        assert assignment.instrument == "violin"
        assert assignment.role == InstrumentRole.MELODY

    def test_roundtrip_dict(self) -> None:
        assignment = InstrumentAssignment(
            instrument="cello",
            section_id="chorus",
            role=InstrumentRole.BASS,
            density_factor=0.7,
        )
        data = assignment.to_dict()
        restored = InstrumentAssignment.from_dict(data)
        assert restored.instrument == "cello"
        assert restored.role == InstrumentRole.BASS
        assert restored.density_factor == 0.7


class TestArrangementPlan:
    """Test ArrangementPlan queries."""

    def _make_plan(self) -> ArrangementPlan:
        return ArrangementPlan(
            assignments=[
                InstrumentAssignment("piano", "verse", InstrumentRole.MELODY),
                InstrumentAssignment("violin", "verse", InstrumentRole.HARMONY),
                InstrumentAssignment("cello", "verse", InstrumentRole.BASS),
                InstrumentAssignment("piano", "chorus", InstrumentRole.HARMONY),
                InstrumentAssignment("violin", "chorus", InstrumentRole.MELODY),
                InstrumentAssignment("cello", "chorus", InstrumentRole.BASS),
                InstrumentAssignment("piano", "bridge", InstrumentRole.SILENT),
            ],
            layer_count_by_section={"verse": 3, "chorus": 3, "bridge": 1},
        )

    def test_assignments_for_section(self) -> None:
        plan = self._make_plan()
        verse = plan.assignments_for_section("verse")
        assert len(verse) == 3

    def test_melody_instrument(self) -> None:
        plan = self._make_plan()
        assert plan.melody_instrument("verse") == "piano"
        assert plan.melody_instrument("chorus") == "violin"
        assert plan.melody_instrument("bridge") is None

    def test_active_instruments(self) -> None:
        plan = self._make_plan()
        assert "piano" not in plan.active_instruments("bridge")
        assert len(plan.active_instruments("verse")) == 3

    def test_roundtrip_dict(self) -> None:
        plan = self._make_plan()
        data = plan.to_dict()
        restored = ArrangementPlan.from_dict(data)
        assert len(restored.assignments) == 7
        assert restored.layer_count_by_section["chorus"] == 3
