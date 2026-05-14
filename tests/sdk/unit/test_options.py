"""Tests for yao.sdk._options — default options builder."""

from __future__ import annotations

from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions

from yao.sdk._options import default_yao_options


class TestDefaultYaoOptions:
    def test_returns_claude_agent_options(self) -> None:
        opts = default_yao_options("test-project")
        assert isinstance(opts, ClaudeAgentOptions)

    def test_system_prompt_preset(self) -> None:
        opts = default_yao_options("test-project")
        assert opts.system_prompt == {"type": "preset", "preset": "claude_code"}

    def test_setting_sources(self) -> None:
        opts = default_yao_options("test-project")
        assert opts.setting_sources == ["project"]

    def test_permission_mode(self) -> None:
        opts = default_yao_options("test-project")
        assert opts.permission_mode == "acceptEdits"

    def test_effort(self) -> None:
        opts = default_yao_options("test-project")
        assert opts.effort == "high"

    def test_skills(self) -> None:
        opts = default_yao_options("test-project")
        assert opts.skills == "all"

    def test_mcp_servers_contains_yao(self) -> None:
        opts = default_yao_options("test-project")
        assert isinstance(opts.mcp_servers, dict)
        assert "yao" in opts.mcp_servers

    def test_allowed_tools(self) -> None:
        opts = default_yao_options("test-project")
        assert "Read" in opts.allowed_tools
        assert "mcp__yao__*" in opts.allowed_tools

    def test_cwd_defaults_to_current(self) -> None:
        opts = default_yao_options("test-project")
        assert opts.cwd == str(Path.cwd())

    def test_cwd_can_be_overridden(self, tmp_path: Path) -> None:
        opts = default_yao_options("test-project", cwd=tmp_path)
        assert opts.cwd == str(tmp_path.resolve())

    def test_extra_options_override(self) -> None:
        extra = ClaudeAgentOptions(effort="low")
        opts = default_yao_options("test-project", extra_options=extra)
        assert opts.effort == "low"
        # Non-overridden values should keep defaults
        assert opts.permission_mode == "acceptEdits"

    def test_extra_options_preserve_mcp(self) -> None:
        """Extra options that don't touch mcp_servers should preserve the yao server."""
        extra = ClaudeAgentOptions(effort="medium")
        opts = default_yao_options("test-project", extra_options=extra)
        assert isinstance(opts.mcp_servers, dict)
        assert "yao" in opts.mcp_servers
