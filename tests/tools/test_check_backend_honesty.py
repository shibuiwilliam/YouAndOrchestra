"""Tests for tools/check_backend_honesty.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))

import check_backend_honesty  # noqa: E402


class TestBackendVisitor:
    """Tests for the AST visitor."""

    def test_detects_fallback_without_is_stub(self, tmp_path: Path) -> None:
        import ast

        source = """
class MyBackend:
    def __init__(self):
        self._fallback = PythonOnlyBackend()

    def invoke(self, role, context, config=None):
        return self._fallback.invoke(role, context)
"""
        tree = ast.parse(source)
        visitor = check_backend_honesty.BackendVisitor(tmp_path / "test.py", source)
        with patch.object(check_backend_honesty, "REPO_ROOT", tmp_path):
            visitor.visit(tree)
        assert len(visitor.backends) == 1
        assert visitor.backends[0].uses_fallback is True
        assert visitor.backends[0].violation is not None

    def test_passes_honest_stub(self, tmp_path: Path) -> None:
        import ast

        source = """
class StubBackend:
    is_stub = True

    def __init__(self):
        self._fallback = PythonOnlyBackend()

    def invoke(self, role, context, config=None):
        return self._fallback.invoke(role, context)
"""
        tree = ast.parse(source)
        visitor = check_backend_honesty.BackendVisitor(tmp_path / "test.py", source)
        with patch.object(check_backend_honesty, "REPO_ROOT", tmp_path):
            visitor.visit(tree)
        assert len(visitor.backends) == 1
        # Has "Stub" in name → no violation
        assert visitor.backends[0].violation is None

    def test_detects_false_is_stub_with_fallback(self, tmp_path: Path) -> None:
        import ast

        source = """
class DishonestBackend:
    is_stub = False

    def __init__(self):
        self._fallback = PythonOnlyBackend()

    def invoke(self, role, context, config=None):
        return self._fallback.invoke(role, context)
"""
        tree = ast.parse(source)
        visitor = check_backend_honesty.BackendVisitor(tmp_path / "test.py", source)
        with patch.object(check_backend_honesty, "REPO_ROOT", tmp_path):
            visitor.visit(tree)
        assert len(visitor.backends) == 1
        assert visitor.backends[0].violation is not None
        assert "is_stub=False" in visitor.backends[0].violation

    def test_passes_python_only_backend(self, tmp_path: Path) -> None:
        import ast

        source = """
class PythonOnlyBackend:
    def invoke(self, role, context, config=None):
        subagent = get_subagent(role)
        return subagent.process(context)
"""
        tree = ast.parse(source)
        visitor = check_backend_honesty.BackendVisitor(tmp_path / "test.py", source)
        with patch.object(check_backend_honesty, "REPO_ROOT", tmp_path):
            visitor.visit(tree)
        assert len(visitor.backends) == 1
        assert visitor.backends[0].violation is None


class TestMainExitCode:
    """Tests for main()."""

    def test_returns_one_on_violation(self, tmp_path: Path) -> None:
        agents_dir = tmp_path / "src" / "yao" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "bad_backend.py").write_text("""
class BadBackend:
    def __init__(self):
        self._fallback = PythonOnlyBackend()

    def invoke(self, role, context, config=None):
        return self._fallback.invoke(role, context)
""")
        with (
            patch.object(check_backend_honesty, "REPO_ROOT", tmp_path),
            patch.object(check_backend_honesty, "AGENTS_DIR", agents_dir),
            patch.object(sys, "argv", ["check_backend_honesty.py"]),
        ):
            result = check_backend_honesty.main()
        assert result == 1

    def test_returns_zero_when_all_honest(self, tmp_path: Path) -> None:
        agents_dir = tmp_path / "src" / "yao" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "python_only_backend.py").write_text("""
class PythonOnlyBackend:
    def invoke(self, role, context, config=None):
        return process(role, context)
""")
        with (
            patch.object(check_backend_honesty, "REPO_ROOT", tmp_path),
            patch.object(check_backend_honesty, "AGENTS_DIR", agents_dir),
            patch.object(sys, "argv", ["check_backend_honesty.py"]),
        ):
            result = check_backend_honesty.main()
        assert result == 0
