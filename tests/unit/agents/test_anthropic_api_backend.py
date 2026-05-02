"""Tests for AnthropicAPIBackend — Wave 1.2.

All tests mock the Anthropic client. No real API calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from yao.agents.protocol import AgentInvocationConfig
from yao.subagents.base import AgentContext, AgentOutput, AgentRole

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_anthropic_module(monkeypatch):
    """Inject a mock anthropic module into the backend module."""
    import yao.agents.anthropic_api_backend as backend_mod

    mock_mod = MagicMock()
    monkeypatch.setattr(backend_mod, "anthropic", mock_mod)
    return mock_mod


def _make_tool_response(tool_input: dict) -> MagicMock:
    """Create a mock API response with a tool_use block."""
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = "submit_output"
    tool_use_block.input = tool_input

    response = MagicMock()
    response.content = [tool_use_block]
    response.usage = MagicMock()
    response.usage.input_tokens = 500
    response.usage.output_tokens = 200
    response.model = "claude-sonnet-4-6"
    response.stop_reason = "tool_use"
    return response


@pytest.fixture()
def mock_client():
    """Create a mock Anthropic client with a successful composer response."""
    client = MagicMock()
    client.messages.create.return_value = _make_tool_response(
        {
            "motif_plan": {
                "seeds": [
                    {
                        "id": "m1",
                        "rhythm_shape": [1.0, 0.5],
                        "interval_shape": [2, -1],
                        "origin_section": "verse",
                        "character": "ascending hook",
                    }
                ],
                "placements": [{"motif_id": "m1", "section_id": "verse", "start_beat": 0.0}],
            },
            "phrase_plan": {"phrases": [], "bars_per_phrase": 4.0, "pattern": "AABA"},
        }
    )
    return client


@pytest.fixture()
def minimal_context():
    """Create a minimal AgentContext for testing."""
    spec = MagicMock()
    spec.title = "Test"
    spec.key = "C"
    spec.tempo = 120
    spec.time_signature = "4/4"

    intent = MagicMock()
    intent.keywords = ["calm"]

    trajectory = MagicMock()

    return AgentContext(spec=spec, intent=intent, trajectory=trajectory)


def _make_backend(mock_anthropic_module, mock_client):
    """Helper to create an AnthropicAPIBackend with mocked client."""
    from yao.agents.anthropic_api_backend import AnthropicAPIBackend

    mock_anthropic_module.Anthropic.return_value = mock_client
    return AnthropicAPIBackend(api_key="test-key-123")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInitialization:
    """Tests for AnthropicAPIBackend.__init__."""

    def test_raises_without_api_key(self, mock_anthropic_module):
        """Backend must raise BackendNotConfiguredError without API key."""
        from yao.agents.anthropic_api_backend import AnthropicAPIBackend
        from yao.errors import BackendNotConfiguredError

        with patch.dict("os.environ", {}, clear=True), pytest.raises(BackendNotConfiguredError):
            AnthropicAPIBackend()

    def test_accepts_explicit_api_key(self, mock_anthropic_module, mock_client):
        """Backend should accept an explicit api_key parameter."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        assert backend.is_stub is False

    def test_accepts_env_var_api_key(self, mock_anthropic_module, mock_client):
        """Backend should accept ANTHROPIC_API_KEY from environment."""
        from yao.agents.anthropic_api_backend import AnthropicAPIBackend

        mock_anthropic_module.Anthropic.return_value = mock_client
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key-456"}):
            backend = AnthropicAPIBackend()
            assert backend.is_stub is False


class TestRolePrompts:
    """Tests for loading .claude/agents/*.md as system prompts."""

    def test_loads_role_prompts(self, mock_anthropic_module, mock_client):
        """Backend must load all 7 role prompt files."""
        backend = _make_backend(mock_anthropic_module, mock_client)

        for role in AgentRole:
            assert role in backend._prompts, f"Missing prompt for {role}"
            assert len(backend._prompts[role]) > 0


class TestContextSerialization:
    """Tests for AgentContext → JSON serialization."""

    def test_serializes_context_correctly(self, mock_anthropic_module, mock_client, minimal_context):
        """Context serialization must produce valid JSON."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        serialized = backend._serialize_context(minimal_context)
        parsed = json.loads(serialized)
        assert "spec" in parsed
        assert "intent" in parsed
        assert "trajectory" in parsed


class TestInvocation:
    """Tests for the invoke() method."""

    def test_parses_tool_use_output(self, mock_anthropic_module, mock_client, minimal_context):
        """invoke() must parse tool_use response into AgentOutput."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        output = backend.invoke(AgentRole.COMPOSER, minimal_context)
        assert isinstance(output, AgentOutput)
        assert output.provenance is not None
        assert output.motif_plan is not None
        assert len(output.motif_plan.seeds) == 1

    def test_records_provenance_with_backend_metadata(self, mock_anthropic_module, mock_client, minimal_context):
        """Provenance must include backend, model, prompt_hash, token_usage."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        output = backend.invoke(AgentRole.COMPOSER, minimal_context)
        records = output.provenance.records

        llm_records = [r for r in records if r.operation == "llm_invocation"]
        assert len(llm_records) == 1
        rec = llm_records[0]
        assert rec.parameters["backend"] == "anthropic_api"
        assert "model" in rec.parameters
        assert "prompt_hash" in rec.parameters
        assert "token_usage" in rec.parameters
        assert rec.parameters["token_usage"]["input"] == 500
        assert rec.parameters["token_usage"]["output"] == 200

    def test_is_stub_returns_false(self, mock_anthropic_module, mock_client):
        """is_stub must be False for the real implementation."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        assert backend.is_stub is False

    def test_no_silent_fallback_on_api_error(self, mock_anthropic_module, minimal_context):
        """API errors must raise, never silently fall back to PythonOnly."""
        from yao.agents.anthropic_api_backend import AnthropicAPIBackend
        from yao.errors import AgentBackendError

        error_client = MagicMock()
        error_client.messages.create.side_effect = Exception("API error")
        mock_anthropic_module.Anthropic.return_value = error_client

        backend = AnthropicAPIBackend(api_key="test-key")
        with pytest.raises(AgentBackendError):
            backend.invoke(AgentRole.COMPOSER, minimal_context)

    def test_passes_config_to_api_call(self, mock_anthropic_module, mock_client, minimal_context):
        """Config max_tokens and temperature must be forwarded to API."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        config = AgentInvocationConfig(max_tokens=2048, temperature=0.7)
        backend.invoke(AgentRole.COMPOSER, minimal_context, config=config)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 2048
        assert call_kwargs["temperature"] == 0.7

    def test_raises_on_missing_tool_use_block(self, mock_anthropic_module, minimal_context):
        """Must raise AgentOutputParseError if no tool_use in response."""
        from yao.agents.anthropic_api_backend import AnthropicAPIBackend
        from yao.errors import AgentOutputParseError

        # Response with no tool_use block
        text_block = MagicMock()
        text_block.type = "text"
        text_block.text = "Here is my output..."

        response = MagicMock()
        response.content = [text_block]
        response.usage = MagicMock()
        response.usage.input_tokens = 100
        response.usage.output_tokens = 50

        client = MagicMock()
        client.messages.create.return_value = response
        mock_anthropic_module.Anthropic.return_value = client

        backend = AnthropicAPIBackend(api_key="test-key")
        with pytest.raises(AgentOutputParseError):
            backend.invoke(AgentRole.COMPOSER, minimal_context)


class TestCostTracking:
    """Tests for cost safety mechanisms."""

    def test_warns_at_100_calls(self, mock_anthropic_module, mock_client, minimal_context):
        """Should emit warning after 100+ LLM calls in a session."""
        backend = _make_backend(mock_anthropic_module, mock_client)
        backend._call_count = 99

        with patch("yao.agents.anthropic_api_backend.logger") as mock_logger:
            backend.invoke(AgentRole.COMPOSER, minimal_context)
            mock_logger.warning.assert_called_once()
