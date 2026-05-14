"""Tests for yao.sdk.permissions — permission policies."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from yao.sdk.permissions import default_yao_permission


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.get_event_loop().run_until_complete(coro)


class TestDefaultPermission:
    def _ctx(self) -> MagicMock:
        return MagicMock()

    def test_allows_normal_read(self) -> None:
        result = _run(default_yao_permission("Read", {"file_path": "src/yao/test.py"}, self._ctx()))
        assert isinstance(result, PermissionResultAllow)

    def test_allows_write_to_outputs(self) -> None:
        result = _run(
            default_yao_permission(
                "Write",
                {"file_path": "outputs/projects/test/iterations/v002/full.mid"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultAllow)

    def test_denies_write_to_claude_agents(self) -> None:
        result = _run(
            default_yao_permission(
                "Write",
                {"file_path": ".claude/agents/composer.md"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)
        assert "does not permit writes" in result.message

    def test_denies_write_to_claude_commands(self) -> None:
        result = _run(
            default_yao_permission(
                "Edit",
                {"file_path": ".claude/commands/compose.md"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)

    def test_denies_write_to_references(self) -> None:
        result = _run(
            default_yao_permission(
                "Write",
                {"file_path": "references/catalog.yaml"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)

    def test_denies_write_to_claude_md(self) -> None:
        result = _run(
            default_yao_permission(
                "Edit",
                {"file_path": "CLAUDE.md"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)

    def test_denies_destructive_bash_outputs(self) -> None:
        result = _run(
            default_yao_permission(
                "Bash",
                {"command": "rm -rf outputs/projects/my-song"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)

    def test_denies_destructive_bash_references(self) -> None:
        result = _run(
            default_yao_permission(
                "Bash",
                {"command": "rm -rf references/"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)

    def test_denies_destructive_bash_claude(self) -> None:
        result = _run(
            default_yao_permission(
                "Bash",
                {"command": "rm -rf .claude/agents"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultDeny)

    def test_allows_safe_bash(self) -> None:
        result = _run(
            default_yao_permission(
                "Bash",
                {"command": "python -m pytest tests/"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultAllow)

    def test_allows_write_to_specs(self) -> None:
        result = _run(
            default_yao_permission(
                "Write",
                {"file_path": "specs/projects/test/composition.yaml"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultAllow)

    def test_allows_mcp_tools(self) -> None:
        result = _run(
            default_yao_permission(
                "mcp__yao__yao_compose",
                {"spec_path": "test.yaml"},
                self._ctx(),
            )
        )
        assert isinstance(result, PermissionResultAllow)
