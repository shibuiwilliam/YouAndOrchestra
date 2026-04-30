"""Tests for RuleBasedHarmonyPlanner."""

from __future__ import annotations

from yao.generators.plan.harmony_planner import RuleBasedHarmonyPlanner
from yao.ir.plan.harmony import CadenceRole, HarmonicFunction
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2

_SPEC_WITH_HARMONY = {
    "version": "2",
    "identity": {"title": "Harmony Test", "duration_sec": 32},
    "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
    "form": {
        "sections": [
            {"id": "verse", "bars": 4, "density": 0.5},
            {"id": "chorus", "bars": 4, "density": 0.9, "climax": True},
        ]
    },
    "harmony": {
        "complexity": 0.5,
        "chord_palette": ["I", "V", "vi", "IV"],
        "cadence": {"verse": "half", "chorus": "authentic"},
        "harmonic_rhythm": {
            "verse": "1 chord per bar",
            "chorus": "2 chords per bar",
        },
    },
    "arrangement": {"instruments": {"piano": {"role": "melody"}}},
}


class TestRuleBasedHarmonyPlanner:
    def test_generates_chord_events(self) -> None:
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, traj, prov)
        assert "harmony" in result
        harmony = result["harmony"]
        # verse: 4 bars × 1 chord + chorus: 4 bars × 2 chords = 12
        assert len(harmony.chord_events) == 12

    def test_cadences_assigned(self) -> None:
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, traj, prov)
        harmony = result["harmony"]
        assert harmony.cadences.get("verse") == CadenceRole.HALF
        assert harmony.cadences.get("chorus") == CadenceRole.AUTHENTIC

    def test_chord_palette_used(self) -> None:
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, traj, prov)
        romans = {c.roman for c in result["harmony"].chord_events}
        # All chords should come from the palette
        assert romans <= {"I", "V", "vi", "IV"}

    def test_harmonic_functions_assigned(self) -> None:
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, traj, prov)
        functions = {c.function for c in result["harmony"].chord_events}
        assert HarmonicFunction.TONIC in functions
        assert HarmonicFunction.DOMINANT in functions

    def test_provenance_recorded(self) -> None:
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        RuleBasedHarmonyPlanner().generate(spec, traj, prov)
        assert any("harmony_planning" in r.operation for r in prov.records)

    def test_default_progression(self) -> None:
        data = {
            "version": "2",
            "identity": {"title": "Default", "duration_sec": 16},
            "global": {"key": "C major", "bpm": 120, "time_signature": "4/4"},
            "form": {"sections": [{"id": "main", "bars": 4, "density": 0.5}]},
            "arrangement": {"instruments": {"piano": {"role": "melody"}}},
        }
        spec = CompositionSpecV2.model_validate(data)
        traj = MultiDimensionalTrajectory.default()
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, traj, prov)
        assert len(result["harmony"].chord_events) == 4
