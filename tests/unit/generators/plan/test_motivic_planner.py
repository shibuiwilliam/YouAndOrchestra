"""Tests for the motivic planner.

Verifies that MotivicPlanner generates coherent MotifPlans
with appropriate seed motifs and section placements.
"""

from __future__ import annotations

from yao.generators.plan.motivic_planner import MotivicPlanner
from yao.ir.plan.motif import MotifTransform
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2


def _make_spec(sections: list[dict[str, object]] | None = None) -> CompositionSpecV2:
    """Create a minimal v2 spec for testing."""
    if sections is None:
        sections = [
            {"id": "intro", "bars": 4, "density": 0.3},
            {"id": "verse", "bars": 8, "density": 0.5},
            {"id": "chorus", "bars": 8, "density": 0.7},
            {"id": "bridge", "bars": 4, "density": 0.5},
            {"id": "outro", "bars": 8, "density": 0.3},
        ]
    # Calculate duration from bars at 120bpm, 4/4
    total_bars = sum(s["bars"] for s in sections)  # type: ignore[arg-type]
    duration_sec = total_bars * 4 * 60 / 120  # bars * beats_per_bar * 60 / bpm
    return CompositionSpecV2.model_validate(
        {
            "version": "2",
            "identity": {"title": "Motif Test", "duration_sec": duration_sec},
            "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
            "form": {"sections": sections},
            "arrangement": {"instruments": {"piano": {"role": "melody"}}},
            "generation": {"strategy": "stochastic", "seed": 42},
        }
    )


class TestMotivicPlannerBasics:
    """Basic tests for MotivicPlanner."""

    def test_generates_non_empty_plan(self) -> None:
        """Planner should generate at least one seed and placements."""
        planner = MotivicPlanner()
        result = planner.generate(_make_spec(), MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]
        assert len(plan.seeds) >= 1
        assert len(plan.placements) >= 1

    def test_primary_motif_in_every_section(self) -> None:
        """Primary motif M1 should appear in every section."""
        planner = MotivicPlanner()
        spec = _make_spec()
        result = planner.generate(spec, MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]

        sections_with_m1 = {p.section_id for p in plan.placements if p.motif_id == "M1"}
        spec_section_ids = {s.id for s in spec.form.sections}
        assert sections_with_m1 == spec_section_ids, f"M1 missing from sections: {spec_section_ids - sections_with_m1}"

    def test_final_section_uses_identity(self) -> None:
        """Last section should return to identity transform for closure."""
        planner = MotivicPlanner()
        spec = _make_spec()
        result = planner.generate(spec, MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]

        last_section_id = spec.form.sections[-1].id
        last_placements = [p for p in plan.placements if p.section_id == last_section_id and p.motif_id == "M1"]
        assert any(p.transform == MotifTransform.IDENTITY for p in last_placements)

    def test_bridge_uses_transformed_motif(self) -> None:
        """Bridge section should use a non-identity transformation."""
        planner = MotivicPlanner()
        spec = _make_spec()
        result = planner.generate(spec, MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]

        bridge_placements = [p for p in plan.placements if p.section_id == "bridge" and p.motif_id == "M1"]
        assert len(bridge_placements) >= 1
        transforms_used = {p.transform for p in bridge_placements}
        # Bridge should not be pure identity
        assert transforms_used != {MotifTransform.IDENTITY}

    def test_secondary_motif_for_long_pieces(self) -> None:
        """Pieces >= 24 bars should get a secondary motif."""
        planner = MotivicPlanner()
        spec = _make_spec()  # 4+8+8+4+8 = 32 bars
        result = planner.generate(spec, MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]

        assert len(plan.seeds) >= 2
        assert any(s.id == "M2" for s in plan.seeds)

    def test_short_piece_single_motif(self) -> None:
        """Short pieces (< 24 bars) should have only one motif."""
        planner = MotivicPlanner()
        short_spec = _make_spec(
            [
                {"id": "verse", "bars": 8, "density": 0.5},
                {"id": "chorus", "bars": 8, "density": 0.7},
            ]
        )
        result = planner.generate(short_spec, MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]

        assert len(plan.seeds) == 1

    def test_seed_has_valid_rhythm(self) -> None:
        """Seed motif rhythm should sum to a reasonable beat count."""
        planner = MotivicPlanner()
        result = planner.generate(_make_spec(), MultiDimensionalTrajectory.default(), ProvenanceLog())
        plan = result["motif"]

        for seed in plan.seeds:
            total = seed.length_beats()
            assert 2.0 <= total <= 8.0, f"Motif {seed.id} has unusual length: {total}"

    def test_provenance_recorded(self) -> None:
        """Planner should record provenance."""
        prov = ProvenanceLog()
        planner = MotivicPlanner()
        planner.generate(_make_spec(), MultiDimensionalTrajectory.default(), prov)
        assert len(prov) > 0

    def test_reproducible_with_same_seed(self) -> None:
        """Same seed should produce identical plans."""
        planner = MotivicPlanner()
        traj = MultiDimensionalTrajectory.default()
        spec = _make_spec()

        result1 = planner.generate(spec, traj, ProvenanceLog())
        result2 = planner.generate(spec, traj, ProvenanceLog())

        plan1 = result1["motif"]
        plan2 = result2["motif"]
        assert len(plan1.seeds) == len(plan2.seeds)
        assert len(plan1.placements) == len(plan2.placements)
