"""Tests for hook critique rules."""

from __future__ import annotations

from tests.helpers import make_minimal_spec_v2
from yao.ir.hook import BarPosition, DeploymentStrategy, Hook, HookPlan
from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec
from yao.verify.critique.hook_rules import (
    HookMisplacementDetector,
    HookOveruseDetector,
    HookUnderuseDetector,
)


def _make_plan(hook_plan: HookPlan | None = None) -> MusicalPlan:
    """Create a minimal MusicalPlan for testing."""
    return MusicalPlan(
        form=SongFormPlan(
            sections=[
                SectionPlan(id="intro", start_bar=0, bars=4, role="intro", target_density=0.3, target_tension=0.2),
                SectionPlan(id="verse", start_bar=4, bars=8, role="verse", target_density=0.5, target_tension=0.4),
                SectionPlan(id="chorus", start_bar=12, bars=8, role="chorus", target_density=0.8, target_tension=0.8),
            ],
            climax_section_id="chorus",
        ),
        harmony=HarmonyPlan(chord_events=[]),
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
        hook_plan=hook_plan,
    )


def _make_spec():
    """Create a minimal CompositionSpecV2 for testing."""
    return make_minimal_spec_v2(
        form={
            "sections": [
                {"id": "intro", "bars": 4},
                {"id": "verse", "bars": 8},
                {"id": "chorus", "bars": 8},
            ]
        },
    )


class TestHookOveruse:
    def test_no_finding_within_limit(self) -> None:
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.FREQUENT,
                    appearances=(
                        BarPosition(section_id="chorus", bar=0),
                        BarPosition(section_id="chorus", bar=4),
                    ),
                    maximum_uses=3,
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookOveruseDetector().detect(plan, _make_spec())
        assert len(findings) == 0

    def test_finding_when_over_limit(self) -> None:
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.FREQUENT,
                    appearances=tuple(BarPosition(section_id="chorus", bar=i) for i in range(5)),
                    maximum_uses=3,
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookOveruseDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "overuse" in findings[0].rule_id

    def test_no_finding_without_hook_plan(self) -> None:
        plan = _make_plan(hook_plan=None)
        findings = HookOveruseDetector().detect(plan, _make_spec())
        assert len(findings) == 0


class TestHookUnderuse:
    def test_no_finding_when_appearances_exist(self) -> None:
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.RARE,
                    appearances=(BarPosition(section_id="chorus", bar=0),),
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookUnderuseDetector().detect(plan, _make_spec())
        assert len(findings) == 0

    def test_finding_when_no_appearances(self) -> None:
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.FREQUENT,
                    appearances=(),
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookUnderuseDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "underuse" in findings[0].rule_id


class TestHookMisplacement:
    def test_no_finding_for_chorus_placement(self) -> None:
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.WITHHOLD_THEN_RELEASE,
                    appearances=(BarPosition(section_id="chorus", bar=0),),
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookMisplacementDetector().detect(plan, _make_spec())
        assert len(findings) == 0

    def test_finding_when_withhold_in_intro(self) -> None:
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.WITHHOLD_THEN_RELEASE,
                    appearances=(BarPosition(section_id="intro", bar=0),),
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookMisplacementDetector().detect(plan, _make_spec())
        assert len(findings) == 1
        assert "misplacement" in findings[0].rule_id
        assert "intro" in findings[0].issue

    def test_no_finding_for_frequent_in_intro(self) -> None:
        """Non-withhold hooks can appear in intro."""
        hook_plan = HookPlan(
            hooks=[
                Hook(
                    id="h1",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.FREQUENT,
                    appearances=(BarPosition(section_id="intro", bar=0),),
                )
            ]
        )
        plan = _make_plan(hook_plan)
        findings = HookMisplacementDetector().detect(plan, _make_spec())
        assert len(findings) == 0
