"""Motif recurrence regression tests.

Verifies that the MotivicPlanner generates motif placements
across all sections, providing theme-and-variation coherence.
"""

from __future__ import annotations

from yao.generators.plan.motivic_planner import MotivicPlanner
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.melody_variation import motif_recurrence_score


def _make_spec(sections: list[tuple[str, int]]) -> CompositionSpecV2:
    """Create a minimal v2 spec with given sections."""
    section_dicts = [{"id": name, "bars": bars} for name, bars in sections]
    return CompositionSpecV2.model_validate(
        {
            "version": "2",
            "identity": {"title": "Test", "duration_sec": 120},
            "global": {"key": "C major", "bpm": 120},
            "form": {"sections": section_dicts},
            "arrangement": {"instruments": {"piano": {"role": "melody"}}},
            "generation": {"strategy": "stochastic", "seed": 42},
        }
    )


def test_motif_recurs_in_all_sections() -> None:
    """Primary motif (M1) should appear in every section."""
    spec = _make_spec(
        [
            ("intro", 4),
            ("verse", 8),
            ("chorus", 8),
            ("bridge", 8),
            ("outro", 4),
        ]
    )
    planner = MotivicPlanner()
    result = planner.generate(
        spec,
        MultiDimensionalTrajectory.default(),
        ProvenanceLog(),
    )
    plan = result["motif"]
    score = motif_recurrence_score(plan)
    # M1 should be in every section (score == 1.0)
    assert score >= 0.8, f"Motif appears in only {score:.0%} of sections"


def test_motif_has_varied_transforms() -> None:
    """Motif placements should use multiple different transforms."""
    spec = _make_spec(
        [
            ("verse", 8),
            ("chorus", 8),
            ("bridge", 8),
            ("outro", 8),
        ]
    )
    planner = MotivicPlanner()
    result = planner.generate(
        spec,
        MultiDimensionalTrajectory.default(),
        ProvenanceLog(),
    )
    plan = result["motif"]
    transforms_used = {p.transform for p in plan.placements if p.motif_id == "M1"}
    # Should use at least 3 different transforms
    assert len(transforms_used) >= 3, f"Only {len(transforms_used)} transforms used: {transforms_used}"


def test_no_plan_returns_zero() -> None:
    """Null plan returns zero recurrence score."""
    assert motif_recurrence_score(None) == 0.0
