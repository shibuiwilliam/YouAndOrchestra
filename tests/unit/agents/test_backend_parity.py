"""Backend parity tests — both backends return the same AgentOutput type.

Verifies that PythonOnlyBackend and AnthropicAPIBackend produce
AgentOutput with the same structural guarantees.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from yao.subagents.base import AgentContext, AgentOutput, AgentRole


@pytest.fixture()
def minimal_context():
    """Create a minimal AgentContext."""
    spec = MagicMock()
    spec.title = "Test"
    spec.key = "C"
    spec.tempo = 120
    spec.time_signature = "4/4"

    intent = MagicMock()
    intent.keywords = ["calm"]

    trajectory = MagicMock()
    return AgentContext(spec=spec, intent=intent, trajectory=trajectory)


class TestBackendParity:
    """Both backends must return AgentOutput with provenance."""

    def test_python_only_returns_agent_output(self):
        """PythonOnlyBackend returns AgentOutput (using a simpler role)."""
        from yao.agents.python_only_backend import PythonOnlyBackend

        # Use ADVERSARIAL_CRITIC which has simpler context requirements
        spec = MagicMock()
        spec.title = "Test"
        spec.key = "C"
        spec.tempo = 120
        spec.time_signature = "4/4"

        intent = MagicMock()
        intent.keywords = ["calm"]

        trajectory = MagicMock()
        trajectory.curves = {}

        context = AgentContext(spec=spec, intent=intent, trajectory=trajectory)
        backend = PythonOnlyBackend()
        # Use a role that's simpler to invoke
        output = backend.invoke(AgentRole.ADVERSARIAL_CRITIC, context)
        assert isinstance(output, AgentOutput)
        assert output.provenance is not None
        assert len(output.provenance) > 0

    def test_anthropic_api_returns_agent_output(self, minimal_context, monkeypatch):
        """AnthropicAPIBackend returns AgentOutput with same shape."""
        import yao.agents.anthropic_api_backend as backend_mod

        mock_anthropic = MagicMock()
        monkeypatch.setattr(backend_mod, "anthropic", mock_anthropic)

        # Mock response
        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "submit_output"
        tool_use_block.input = {
            "motif_plan": {
                "seeds": [{"id": "m1", "rhythm_shape": [1.0], "interval_shape": [0], "origin_section": "verse"}],
                "placements": [],
            },
        }
        response = MagicMock()
        response.content = [tool_use_block]
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50

        client = MagicMock()
        client.messages.create.return_value = response
        mock_anthropic.Anthropic.return_value = client

        from yao.agents.anthropic_api_backend import AnthropicAPIBackend

        backend = AnthropicAPIBackend(api_key="test-key")
        output = backend.invoke(AgentRole.COMPOSER, minimal_context)

        assert isinstance(output, AgentOutput)
        assert output.provenance is not None
        assert len(output.provenance) > 0

    def test_both_backends_have_is_stub_attribute(self, monkeypatch):
        """Both backends expose an is_stub attribute for honesty checks."""
        import yao.agents.anthropic_api_backend as backend_mod

        mock_anthropic = MagicMock()
        monkeypatch.setattr(backend_mod, "anthropic", mock_anthropic)
        mock_anthropic.Anthropic.return_value = MagicMock()

        from yao.agents.anthropic_api_backend import AnthropicAPIBackend
        from yao.agents.python_only_backend import PythonOnlyBackend

        api_backend = AnthropicAPIBackend(api_key="test-key")
        assert api_backend.is_stub is False

        # PythonOnly doesn't need is_stub (it's the real deal, not an LLM wrapper)
        python_backend = PythonOnlyBackend()
        assert not getattr(python_backend, "is_stub", False)
