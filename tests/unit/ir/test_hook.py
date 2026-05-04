"""Tests for Hook IR."""

from __future__ import annotations

from yao.ir.hook import (
    BarPosition,
    DeploymentStrategy,
    Hook,
    HookPlan,
)


class TestBarPosition:
    def test_creation(self) -> None:
        pos = BarPosition(section_id="chorus", bar=2)
        assert pos.section_id == "chorus"
        assert pos.bar == 2

    def test_serialization_round_trip(self) -> None:
        pos = BarPosition(section_id="verse", bar=3)
        assert BarPosition.from_dict(pos.to_dict()) == pos


class TestHook:
    def test_basic_creation(self) -> None:
        hook = Hook(
            id="main_hook",
            motif_ref="M1",
            deployment=DeploymentStrategy.WITHHOLD_THEN_RELEASE,
            appearances=(
                BarPosition(section_id="chorus_1", bar=0),
                BarPosition(section_id="chorus_2", bar=0),
            ),
            maximum_uses=3,
            distinctive_strength=0.9,
        )
        assert hook.id == "main_hook"
        assert hook.deployment == DeploymentStrategy.WITHHOLD_THEN_RELEASE
        assert hook.appearance_count() == 2
        assert hook.distinctive_strength == 0.9

    def test_appears_in_section(self) -> None:
        hook = Hook(
            id="h1",
            motif_ref="M1",
            deployment=DeploymentStrategy.FREQUENT,
            appearances=(
                BarPosition(section_id="chorus", bar=0),
                BarPosition(section_id="outro", bar=2),
            ),
        )
        assert hook.appears_in_section("chorus")
        assert hook.appears_in_section("outro")
        assert not hook.appears_in_section("intro")

    def test_first_appearance_section(self) -> None:
        hook = Hook(
            id="h1",
            motif_ref="M1",
            deployment=DeploymentStrategy.RARE,
            appearances=(BarPosition(section_id="bridge", bar=4),),
        )
        assert hook.first_appearance_section() == "bridge"

    def test_first_appearance_none_when_empty(self) -> None:
        hook = Hook(id="h1", motif_ref="M1", deployment=DeploymentStrategy.RARE)
        assert hook.first_appearance_section() is None

    def test_serialization_round_trip(self) -> None:
        hook = Hook(
            id="main_hook",
            motif_ref="M1",
            deployment=DeploymentStrategy.ASCENDING_REPETITION,
            appearances=(
                BarPosition(section_id="chorus_1", bar=0),
                BarPosition(section_id="chorus_2", bar=0),
            ),
            variations_allowed=False,
            maximum_uses=2,
            distinctive_strength=0.75,
        )
        restored = Hook.from_dict(hook.to_dict())
        assert restored.id == hook.id
        assert restored.deployment == hook.deployment
        assert restored.appearance_count() == 2
        assert restored.variations_allowed is False
        assert restored.maximum_uses == 2
        assert restored.distinctive_strength == 0.75


class TestHookPlan:
    def _make_plan(self) -> HookPlan:
        return HookPlan(
            hooks=[
                Hook(
                    id="primary",
                    motif_ref="M1",
                    deployment=DeploymentStrategy.FREQUENT,
                    appearances=(
                        BarPosition(section_id="chorus_1", bar=0),
                        BarPosition(section_id="chorus_2", bar=0),
                    ),
                ),
                Hook(
                    id="secondary",
                    motif_ref="M2",
                    deployment=DeploymentStrategy.RARE,
                    appearances=(BarPosition(section_id="bridge", bar=4),),
                ),
            ]
        )

    def test_hook_by_id(self) -> None:
        plan = self._make_plan()
        assert plan.hook_by_id("primary") is not None
        assert plan.hook_by_id("primary").motif_ref == "M1"
        assert plan.hook_by_id("nonexistent") is None

    def test_hooks_in_section(self) -> None:
        plan = self._make_plan()
        chorus_hooks = plan.hooks_in_section("chorus_1")
        assert len(chorus_hooks) == 1
        assert chorus_hooks[0].id == "primary"

    def test_total_appearances(self) -> None:
        plan = self._make_plan()
        assert plan.total_appearances() == 3

    def test_serialization_round_trip(self) -> None:
        plan = self._make_plan()
        restored = HookPlan.from_dict(plan.to_dict())
        assert len(restored.hooks) == 2
        assert restored.hooks[0].id == "primary"
        assert restored.hooks[1].deployment == DeploymentStrategy.RARE
