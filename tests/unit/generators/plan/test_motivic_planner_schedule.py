"""Tests for enhanced MotivicPlanner with motif schedule."""

from __future__ import annotations

from yao.generators.plan.motivic_planner import MotivicPlanner
from yao.ir.plan.motif import MotifTransform
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2


def _make_spec(sections: list[tuple[str, int]]) -> CompositionSpecV2:
    """Create a minimal v2 spec with given sections."""
    section_dicts = [{"id": name, "bars": bars} for name, bars in sections]
    return CompositionSpecV2.model_validate(
        {
            "version": "2",
            "identity": {"title": "Test", "duration_sec": 60},
            "global": {"key": "C major", "bpm": 120},
            "form": {"sections": section_dicts},
            "arrangement": {"instruments": {"piano": {"role": "melody"}}},
            "generation": {"strategy": "stochastic", "seed": 42},
        }
    )


class TestMotifSchedule:
    """Test motif schedule placement."""

    def test_eight_bar_section_has_multiple_placements(self) -> None:
        spec = _make_spec([("verse", 8), ("chorus", 8)])
        planner = MotivicPlanner()
        result = planner.generate(
            spec,
            MultiDimensionalTrajectory.default(),
            ProvenanceLog(),
        )
        plan = result["motif"]
        verse_placements = plan.placements_in_section("verse")
        # 8 bars // 2 = 4 presentations minimum
        assert len(verse_placements) >= 4

    def test_first_placement_is_identity(self) -> None:
        spec = _make_spec([("verse", 8), ("chorus", 8)])
        planner = MotivicPlanner()
        result = planner.generate(
            spec,
            MultiDimensionalTrajectory.default(),
            ProvenanceLog(),
        )
        plan = result["motif"]
        verse_placements = [p for p in plan.placements_in_section("verse") if p.motif_id == "M1"]
        assert verse_placements[0].transform == MotifTransform.IDENTITY

    def test_final_section_ends_with_identity(self) -> None:
        spec = _make_spec([("verse", 8), ("chorus", 8), ("outro", 8)])
        planner = MotivicPlanner()
        result = planner.generate(
            spec,
            MultiDimensionalTrajectory.default(),
            ProvenanceLog(),
        )
        plan = result["motif"]
        outro_m1 = [p for p in plan.placements_in_section("outro") if p.motif_id == "M1"]
        # Last placement in final section should be IDENTITY or ORNAMENT_REMOVE
        last = outro_m1[-1]
        assert last.transform in (MotifTransform.IDENTITY, MotifTransform.ORNAMENT_REMOVE)

    def test_long_piece_has_secondary_motif(self) -> None:
        spec = _make_spec([("verse", 8), ("chorus", 8), ("bridge", 8)])
        planner = MotivicPlanner()
        result = planner.generate(
            spec,
            MultiDimensionalTrajectory.default(),
            ProvenanceLog(),
        )
        plan = result["motif"]
        assert len(plan.seeds) >= 2
        m2_placements = [p for p in plan.placements if p.motif_id == "M2"]
        assert len(m2_placements) > 0

    def test_short_section_has_at_least_two_placements(self) -> None:
        spec = _make_spec([("verse", 8), ("chorus", 8)])
        planner = MotivicPlanner()
        result = planner.generate(
            spec,
            MultiDimensionalTrajectory.default(),
            ProvenanceLog(),
        )
        plan = result["motif"]
        assert len(plan.placements) >= 2

    def test_bridge_uses_varied_transforms(self) -> None:
        spec = _make_spec([("verse", 8), ("bridge", 16), ("chorus", 8)])
        planner = MotivicPlanner()
        result = planner.generate(
            spec,
            MultiDimensionalTrajectory.default(),
            ProvenanceLog(),
        )
        plan = result["motif"]
        bridge_m1 = [p for p in plan.placements_in_section("bridge") if p.motif_id == "M1"]
        transforms_used = {p.transform for p in bridge_m1}
        # Bridge should use varied transforms, not all identity
        assert len(transforms_used) >= 2
