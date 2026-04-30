"""Tests for RuleBasedFormPlanner."""

from __future__ import annotations

from yao.generators.plan.form_planner import RuleBasedFormPlanner
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2

_MINIMAL_V2 = {
    "version": "2",
    "identity": {"title": "Form Test", "duration_sec": 32},
    "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
    "form": {
        "sections": [
            {"id": "intro", "bars": 4, "density": 0.2},
            {"id": "verse", "bars": 8, "density": 0.5},
            {"id": "chorus", "bars": 8, "density": 0.9, "climax": True},
        ]
    },
    "arrangement": {"instruments": {"piano": {"role": "melody"}}},
}


class TestRuleBasedFormPlanner:
    def test_generates_form_plan(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedFormPlanner().generate(spec, traj, prov)
        assert "form" in result
        form = result["form"]
        assert form.total_bars() == 20
        assert len(form.sections) == 3

    def test_climax_detected(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedFormPlanner().generate(spec, traj, prov)
        assert result["form"].climax_section_id == "chorus"

    def test_section_roles_inferred(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedFormPlanner().generate(spec, traj, prov)
        sections = result["form"].sections
        assert sections[0].role == "intro"
        assert sections[1].role == "verse"
        assert sections[2].role == "chorus"

    def test_start_bars_cumulative(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedFormPlanner().generate(spec, traj, prov)
        sections = result["form"].sections
        assert sections[0].start_bar == 0
        assert sections[1].start_bar == 4
        assert sections[2].start_bar == 12

    def test_provenance_recorded(self) -> None:
        spec = CompositionSpecV2.model_validate(_MINIMAL_V2)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        RuleBasedFormPlanner().generate(spec, traj, prov)
        assert len(prov.records) >= 1
        assert any("form_planning" in r.operation for r in prov.records)

    def test_no_climax_defaults_to_last(self) -> None:
        data = {
            **_MINIMAL_V2,
            "form": {
                "sections": [
                    {"id": "a", "bars": 4, "density": 0.5},
                    {"id": "b", "bars": 4, "density": 0.5},
                ]
            },
        }
        spec = CompositionSpecV2.model_validate(data)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedFormPlanner().generate(spec, traj, prov)
        assert result["form"].climax_section_id == "b"
