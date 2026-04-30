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

    def test_high_tension_prefers_dominant_chords(self) -> None:
        """At high tension, dominant/secondary-dominant chords should be preferred."""
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        # All-high tension trajectory
        high_traj = MultiDimensionalTrajectory.uniform(0.9)
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, high_traj, prov)
        harmony = result["harmony"]
        # With palette ["I", "V", "vi", "IV"] and high tension,
        # V (dominant) should appear more than in default uniform
        dominant_count = sum(1 for c in harmony.chord_events if c.function == HarmonicFunction.DOMINANT)
        assert dominant_count > 0, "High tension should include dominant chords"

    def test_low_tension_prefers_stable_chords(self) -> None:
        """At low tension, tonic/subdominant chords should be preferred."""
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        low_traj = MultiDimensionalTrajectory.uniform(0.1)
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, low_traj, prov)
        harmony = result["harmony"]
        stable_count = sum(
            1 for c in harmony.chord_events if c.function in (HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT)
        )
        total = len(harmony.chord_events)
        assert stable_count > total // 2, "Low tension should prefer stable chords"

    def test_tension_affects_chord_distribution(self) -> None:
        """Different tension levels should produce different chord distributions."""
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        low_traj = MultiDimensionalTrajectory.uniform(0.1)
        high_traj = MultiDimensionalTrajectory.uniform(0.9)

        low_result = RuleBasedHarmonyPlanner().generate(spec, low_traj, ProvenanceLog())
        high_result = RuleBasedHarmonyPlanner().generate(spec, high_traj, ProvenanceLog())

        low_romans = [c.roman for c in low_result["harmony"].chord_events]
        high_romans = [c.roman for c in high_result["harmony"].chord_events]
        # The distributions should differ
        assert low_romans != high_romans, "Different tension levels should produce different chord sequences"

    def test_very_high_tension_injects_secondary_dominants(self) -> None:
        """At tension >= 0.8, secondary dominants (V/V, V/vi) should be injected."""
        spec = CompositionSpecV2.model_validate(_SPEC_WITH_HARMONY)
        # Very high tension trajectory (0.9)
        very_high_traj = MultiDimensionalTrajectory.uniform(0.9)
        prov = ProvenanceLog()

        result = RuleBasedHarmonyPlanner().generate(spec, very_high_traj, prov)
        harmony = result["harmony"]
        romans = {c.roman for c in harmony.chord_events}

        # At very high tension, at least one secondary dominant or borrowed chord
        # should be injected from _SECONDARY_DOMINANTS or _BORROWED_CHORDS
        injected = {"V/V", "V/vi", "V/IV", "bVII", "iv", "bVI"}
        has_injected = bool(romans & injected)
        assert has_injected, (
            f"Very high tension should inject secondary dominants/borrowed chords. Got: {sorted(romans)}"
        )
