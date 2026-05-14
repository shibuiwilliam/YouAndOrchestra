"""Integration test: verify default_yao_options wires all components correctly.

This test validates §5.3 — that the options builder produces a
ClaudeAgentOptions with hooks, agents, permissions, MCP server,
and all other required fields wired together.
"""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from yao.sdk._options import default_yao_options


class TestOptionsWiringIntegration:
    """Verify the full wiring of default_yao_options."""

    def test_all_required_fields_present(self) -> None:
        opts = default_yao_options("test")
        # §5.3 checklist
        assert opts.system_prompt == {"type": "preset", "preset": "claude_code"}
        assert opts.setting_sources == ["project"]
        assert isinstance(opts.mcp_servers, dict)
        assert "yao" in opts.mcp_servers
        assert opts.agents is not None
        assert opts.hooks is not None
        assert opts.can_use_tool is not None
        assert opts.permission_mode == "acceptEdits"
        assert opts.effort == "high"
        assert opts.skills == "all"

    def test_agents_are_agent_definitions(self) -> None:
        opts = default_yao_options("test")
        assert opts.agents is not None
        for name, defn in opts.agents.items():
            assert isinstance(defn, AgentDefinition), f"{name} is not AgentDefinition"

    def test_core_seven_agents_present(self) -> None:
        opts = default_yao_options("test")
        assert opts.agents is not None
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
            assert name in opts.agents, f"Missing agent: {name}"

    def test_hooks_have_pre_and_post(self) -> None:
        opts = default_yao_options("test")
        assert opts.hooks is not None
        assert "PreToolUse" in opts.hooks
        assert "PostToolUse" in opts.hooks
        assert len(opts.hooks["PreToolUse"]) >= 1
        assert len(opts.hooks["PostToolUse"]) >= 2

    def test_can_use_tool_is_callable(self) -> None:
        opts = default_yao_options("test")
        assert callable(opts.can_use_tool)

    def test_mcp_server_has_sdk_type(self) -> None:
        opts = default_yao_options("test")
        assert isinstance(opts.mcp_servers, dict)
        yao_server = opts.mcp_servers["yao"]
        assert yao_server["type"] == "sdk"
        assert yao_server["name"] == "yao"

    def test_extra_options_override_preserves_wiring(self) -> None:
        """Overriding effort should not remove hooks/agents/permissions."""
        extra = ClaudeAgentOptions(effort="low")
        opts = default_yao_options("test", extra_options=extra)
        assert opts.effort == "low"
        # Critical wiring must survive merge
        assert opts.agents is not None
        assert opts.hooks is not None
        assert opts.can_use_tool is not None
