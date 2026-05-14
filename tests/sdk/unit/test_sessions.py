"""Tests for yao.sdk.sessions — project-scoped session helpers."""

from __future__ import annotations

from pathlib import Path

from yao.sdk.sessions import session_project_key


class TestSessionProjectKey:
    def test_returns_resolved_path(self, tmp_path: Path) -> None:
        key = session_project_key(tmp_path)
        assert key == str(tmp_path.resolve())

    def test_relative_path_resolved(self) -> None:
        key = session_project_key(Path("."))
        assert key == str(Path.cwd())
