"""Integration test: permission policies block destructive operations.

§17.4: A test agent attempts rm -rf outputs/ and Write to references/.
Both must be blocked with PermissionResultDeny.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny

from yao.sdk.permissions import default_yao_permission


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.get_event_loop().run_until_complete(coro)


def _ctx() -> MagicMock:
    return MagicMock()


class TestProtectedPathDenials:
    """Every protected path must be denied for Write and Edit."""

    def test_deny_write_claude_agents(self) -> None:
        result = _run(default_yao_permission("Write", {"file_path": ".claude/agents/composer.md"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_edit_claude_commands(self) -> None:
        result = _run(default_yao_permission("Edit", {"file_path": ".claude/commands/compose.md"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_write_claude_skills(self) -> None:
        result = _run(default_yao_permission("Write", {"file_path": ".claude/skills/genres/cinematic.md"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_write_references(self) -> None:
        result = _run(default_yao_permission("Write", {"file_path": "references/catalog.yaml"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_edit_claude_md(self) -> None:
        result = _run(default_yao_permission("Edit", {"file_path": "CLAUDE.md"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)


class TestDestructiveBashDenials:
    """rm -rf against protected directories must be blocked."""

    def test_deny_rm_rf_outputs(self) -> None:
        result = _run(default_yao_permission("Bash", {"command": "rm -rf outputs/projects/test"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_rm_rf_references(self) -> None:
        result = _run(default_yao_permission("Bash", {"command": "rm -rf references/"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_rm_rf_claude_dir(self) -> None:
        result = _run(default_yao_permission("Bash", {"command": "rm -rf .claude/"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)

    def test_deny_rm_r_variant(self) -> None:
        result = _run(default_yao_permission("Bash", {"command": "rm -r outputs/test"}, _ctx()))
        assert isinstance(result, PermissionResultDeny)


class TestAllowedOperations:
    """Normal operations must be allowed."""

    def test_allow_read_anything(self) -> None:
        result = _run(default_yao_permission("Read", {"file_path": ".claude/agents/composer.md"}, _ctx()))
        assert isinstance(result, PermissionResultAllow)

    def test_allow_write_to_specs(self) -> None:
        result = _run(default_yao_permission("Write", {"file_path": "specs/projects/test/composition.yaml"}, _ctx()))
        assert isinstance(result, PermissionResultAllow)

    def test_allow_write_to_outputs_new_iteration(self) -> None:
        result = _run(
            default_yao_permission("Write", {"file_path": "outputs/projects/test/iterations/v002/full.mid"}, _ctx())
        )
        assert isinstance(result, PermissionResultAllow)

    def test_allow_safe_bash(self) -> None:
        result = _run(default_yao_permission("Bash", {"command": "python -m pytest tests/unit/"}, _ctx()))
        assert isinstance(result, PermissionResultAllow)

    def test_allow_mcp_tools(self) -> None:
        result = _run(default_yao_permission("mcp__yao__yao_compose", {"spec_path": "test.yaml"}, _ctx()))
        assert isinstance(result, PermissionResultAllow)

    def test_allow_glob(self) -> None:
        result = _run(default_yao_permission("Glob", {"pattern": "src/**/*.py"}, _ctx()))
        assert isinstance(result, PermissionResultAllow)
