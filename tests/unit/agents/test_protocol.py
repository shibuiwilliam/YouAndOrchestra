"""Tests for Agent Protocol and backend registry."""

from __future__ import annotations

import os

from yao.agents.protocol import AgentBackend, AgentInvocationConfig
from yao.agents.python_only_backend import PythonOnlyBackend
from yao.agents.registry import available_backends, get_backend
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.schema.intent import IntentSpec
from yao.subagents.base import AgentContext, AgentOutput, AgentRole


def _make_context() -> AgentContext:
    spec = CompositionSpec(
        title="Protocol Test",
        key="C major",
        tempo_bpm=120.0,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="rule_based", seed=42),
    )
    return AgentContext(
        spec=spec,
        intent=IntentSpec(text="test", keywords=["test"]),
        trajectory=MultiDimensionalTrajectory.default(),
    )


class TestPythonOnlyBackendSatisfiesProtocol:
    def test_is_agent_backend(self) -> None:
        backend = PythonOnlyBackend()
        assert isinstance(backend, AgentBackend)

    def test_invoke_returns_agent_output(self) -> None:
        backend = PythonOnlyBackend()
        out = backend.invoke(AgentRole.COMPOSER, _make_context())
        assert isinstance(out, AgentOutput)
        assert len(out.provenance) > 0

    def test_all_roles_invocable(self) -> None:
        backend = PythonOnlyBackend()
        ctx = _make_context()
        for role in AgentRole:
            out = backend.invoke(role, ctx)
            assert isinstance(out, AgentOutput)

    def test_config_accepted(self) -> None:
        backend = PythonOnlyBackend()
        config = AgentInvocationConfig(timeout_sec=10.0, max_tokens=2048)
        out = backend.invoke(AgentRole.COMPOSER, _make_context(), config)
        assert isinstance(out, AgentOutput)


class TestRegistry:
    def test_default_is_python_only(self) -> None:
        # Ensure env var is not set
        old = os.environ.pop("YAO_AGENT_BACKEND", None)
        try:
            backend = get_backend()
            assert isinstance(backend, PythonOnlyBackend)
        finally:
            if old is not None:
                os.environ["YAO_AGENT_BACKEND"] = old

    def test_explicit_python_only(self) -> None:
        backend = get_backend("python_only")
        assert isinstance(backend, PythonOnlyBackend)

    def test_available_backends(self) -> None:
        backends = available_backends()
        assert "python_only" in backends
        assert "anthropic_api" in backends
        assert "claude_code" in backends

    def test_unknown_backend_raises(self) -> None:
        import pytest

        with pytest.raises(KeyError, match="Unknown agent backend"):
            get_backend("nonexistent")

    def test_env_var_override(self) -> None:
        old = os.environ.get("YAO_AGENT_BACKEND")
        os.environ["YAO_AGENT_BACKEND"] = "anthropic_api"
        try:
            from yao.agents.anthropic_api_backend import AnthropicAPIBackend

            backend = get_backend()
            assert isinstance(backend, AnthropicAPIBackend)
        finally:
            if old is not None:
                os.environ["YAO_AGENT_BACKEND"] = old
            else:
                os.environ.pop("YAO_AGENT_BACKEND", None)
