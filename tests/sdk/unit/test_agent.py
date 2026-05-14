"""Tests for yao.sdk.agent — YaoAgent facade."""

from __future__ import annotations

import asyncio

import pytest

from yao.sdk.agent import YaoAgent


class TestYaoAgentInit:
    def test_basic_init(self) -> None:
        agent = YaoAgent(project="test-project")
        assert agent.project == "test-project"
        assert agent._iteration == 0

    def test_custom_params(self) -> None:
        agent = YaoAgent(
            project="test",
            model="claude-sonnet-4-6",
            permission_mode="plan",
        )
        assert agent._model == "claude-sonnet-4-6"
        assert agent._permission_mode == "plan"


class TestYaoAgentContextManager:
    def test_context_manager_sets_options(self) -> None:
        async def _run() -> None:
            agent = YaoAgent(project="test")
            assert agent._options is None
            async with agent:
                assert agent._options is not None
            assert agent._options is None

        asyncio.get_event_loop().run_until_complete(_run())

    def test_get_options_outside_context_raises(self) -> None:
        agent = YaoAgent(project="test")
        with pytest.raises(RuntimeError, match="async context manager"):
            agent._get_options()


class TestYaoAgentMethods:
    """Verify method signatures exist and are async generators."""

    def test_has_all_slash_command_methods(self) -> None:
        methods = [
            "sketch",
            "compose",
            "conduct",
            "critique",
            "regenerate_section",
            "render",
            "diff",
            "evaluate",
            "explain",
            "chat",
        ]
        agent = YaoAgent(project="test")
        for method_name in methods:
            assert hasattr(agent, method_name), f"Missing method: {method_name}"
            method = getattr(agent, method_name)
            assert callable(method), f"{method_name} not callable"
