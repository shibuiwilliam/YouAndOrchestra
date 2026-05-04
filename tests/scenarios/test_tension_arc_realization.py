"""Scenario test: Tension arcs are properly structured and validated.

Tests that tension arcs integrate correctly with HarmonyPlan and
that cross-spec validation catches mismatches.
"""

from __future__ import annotations

from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.tension_arc import ArcLocation, ArcRelease, TensionArc, TensionPattern
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec
from yao.schema.tension_arcs import TensionArcsSpec


class TestTensionArcRealizationScenarios:
    """Scenario tests for tension arc integration."""

    def test_arcs_survive_plan_round_trip(self) -> None:
        """TensionArcs survive MusicalPlan serialization round-trip."""
        arc = TensionArc(
            id="approach_chorus",
            location=ArcLocation(section="verse", bar_start=5, bar_end=8),
            pattern=TensionPattern.LINEAR_RISE,
            target_release=ArcRelease(section="chorus", bar=1),
            intensity=0.8,
            mechanism="secondary_dominant_chain",
        )
        harmony = HarmonyPlan(
            chord_events=[
                ChordEvent("verse", 0.0, 32.0, "I", HarmonicFunction.TONIC, 0.4),
                ChordEvent("chorus", 32.0, 32.0, "IV", HarmonicFunction.SUBDOMINANT, 0.6),
            ],
            tension_arcs=(arc,),
        )
        plan = MusicalPlan(
            form=SongFormPlan(
                sections=[
                    SectionPlan("verse", 0, 8, "verse", 0.5, 0.4),
                    SectionPlan("chorus", 8, 8, "chorus", 0.7, 0.7),
                ],
                climax_section_id="chorus",
            ),
            harmony=harmony,
            trajectory=MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text="test", keywords=[]),
            provenance=ProvenanceLog(),
        )

        json_str = plan.to_json()
        restored = MusicalPlan.from_json(json_str)

        assert len(restored.harmony.tension_arcs) == 1
        assert restored.harmony.tension_arcs[0].id == "approach_chorus"
        assert restored.harmony.tension_arcs[0].intensity == 0.8

    def test_spec_to_ir_conversion(self) -> None:
        """TensionArcsSpec can be converted to TensionArc IR objects."""
        spec = TensionArcsSpec.model_validate(
            {
                "tension_arcs": [
                    {
                        "id": "buildup",
                        "location": {"section": "verse", "bars": [5, 8]},
                        "pattern": "linear_rise",
                        "target_release": {"section": "chorus", "bar": 1},
                        "intensity": 0.7,
                        "mechanism": "dominant_prolongation",
                    },
                ],
            }
        )

        # Convert spec to IR
        arcs = []
        for arc_spec in spec.tension_arcs:
            arcs.append(
                TensionArc(
                    id=arc_spec.id,
                    location=ArcLocation(
                        section=arc_spec.location.section,
                        bar_start=arc_spec.location.bars[0],
                        bar_end=arc_spec.location.bars[1],
                    ),
                    pattern=TensionPattern(arc_spec.pattern),
                    target_release=(
                        ArcRelease(
                            section=arc_spec.target_release.section,
                            bar=arc_spec.target_release.bar,
                        )
                        if arc_spec.target_release
                        else None
                    ),
                    intensity=arc_spec.intensity,
                    mechanism=arc_spec.mechanism,
                )
            )

        assert len(arcs) == 1
        assert arcs[0].id == "buildup"
        assert arcs[0].location.span() == 4

    def test_cross_spec_validation_catches_mismatch(self) -> None:
        """Cross-spec validation finds unknown section references."""
        spec = TensionArcsSpec.model_validate(
            {
                "tension_arcs": [
                    {
                        "id": "bad_ref",
                        "location": {"section": "nonexistent", "bars": [1, 4]},
                        "pattern": "spike",
                        "intensity": 0.5,
                    },
                ],
            }
        )
        errors = spec.validate_against_sections(["verse", "chorus"])
        assert len(errors) == 1

    def test_multiple_arcs_per_section(self) -> None:
        """Multiple tension arcs can coexist in the same section."""
        harmony = HarmonyPlan(
            tension_arcs=(
                TensionArc(
                    id="early",
                    location=ArcLocation(section="verse", bar_start=1, bar_end=4),
                    pattern=TensionPattern.DIP,
                    target_release=ArcRelease(section="verse", bar=4),
                    intensity=0.4,
                ),
                TensionArc(
                    id="late",
                    location=ArcLocation(section="verse", bar_start=5, bar_end=8),
                    pattern=TensionPattern.LINEAR_RISE,
                    target_release=ArcRelease(section="chorus", bar=1),
                    intensity=0.7,
                ),
            ),
        )
        verse_arcs = harmony.tension_arcs_in_section("verse")
        assert len(verse_arcs) == 2
