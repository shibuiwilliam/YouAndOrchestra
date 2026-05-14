"""Tests for yao.sdk.agents — programmatic agent definitions."""

from __future__ import annotations

from pathlib import Path

from claude_agent_sdk import AgentDefinition

from yao.sdk.agents import yao_agent_definitions


class TestYaoAgentDefinitions:
    def test_returns_dict_of_agent_definitions(self) -> None:
        defs = yao_agent_definitions()
        assert isinstance(defs, dict)
        for name, defn in defs.items():
            assert isinstance(name, str)
            assert isinstance(defn, AgentDefinition)

    def test_contains_core_agents(self) -> None:
        defs = yao_agent_definitions()
        expected = {
            "composer",
            "harmony-theorist",
            "rhythm-architect",
            "orchestrator",
            "mix-engineer",
            "adversarial-critic",
            "producer",
        }
        for name in expected:
            assert name in defs, f"Missing agent: {name}"

    def test_skips_protocol_files(self) -> None:
        defs = yao_agent_definitions()
        for name in defs:
            assert not name.startswith("_"), f"Protocol file not skipped: {name}"

    def test_adversarial_critic_has_disallowed_tools(self) -> None:
        defs = yao_agent_definitions()
        critic = defs.get("adversarial-critic")
        assert critic is not None
        assert critic.disallowedTools is not None
        assert "Write" in critic.disallowedTools
        assert "Edit" in critic.disallowedTools

    def test_all_agents_have_descriptions(self) -> None:
        defs = yao_agent_definitions()
        for name, defn in defs.items():
            assert defn.description, f"Agent {name} has empty description"

    def test_all_agents_have_prompts(self) -> None:
        defs = yao_agent_definitions()
        for name, defn in defs.items():
            assert defn.prompt, f"Agent {name} has empty prompt"

    def test_all_agents_have_yao_mcp_server(self) -> None:
        defs = yao_agent_definitions()
        for name, defn in defs.items():
            assert defn.mcpServers is not None
            assert "yao" in defn.mcpServers, f"Agent {name} missing yao MCP server"

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        defs = yao_agent_definitions(agents_dir=tmp_path)
        assert defs == {}

    def test_nonexistent_dir_returns_empty(self) -> None:
        defs = yao_agent_definitions(agents_dir=Path("/nonexistent"))
        assert defs == {}

    def test_composer_has_restricted_tools(self) -> None:
        """§7.2: Composer gets specific tool allowlist."""
        defs = yao_agent_definitions()
        composer = defs.get("composer")
        assert composer is not None
        assert composer.tools is not None
        assert "mcp__yao__yao_compose" in composer.tools
        assert "Read" in composer.tools

    def test_critic_has_read_only_tools(self) -> None:
        """§7.2: Critic is read-only, no write tools."""
        defs = yao_agent_definitions()
        critic = defs.get("adversarial-critic")
        assert critic is not None
        assert critic.tools is not None
        assert "Read" in critic.tools
        assert "Write" not in critic.tools
        assert "Edit" not in critic.tools

    def test_producer_has_full_access(self) -> None:
        """§7.2: Producer gets Write, Edit, Agent, mcp__yao__*."""
        defs = yao_agent_definitions()
        producer = defs.get("producer")
        assert producer is not None
        assert producer.tools is not None
        assert "Write" in producer.tools
        assert "Agent" in producer.tools

    def test_producer_effort_high(self) -> None:
        """§7.3: Producer defaults to effort='high'."""
        defs = yao_agent_definitions()
        producer = defs.get("producer")
        assert producer is not None
        assert producer.effort == "high"

    def test_critic_effort_medium(self) -> None:
        """§7.3: Critic defaults to effort='medium'."""
        defs = yao_agent_definitions()
        critic = defs.get("adversarial-critic")
        assert critic is not None
        assert critic.effort == "medium"
