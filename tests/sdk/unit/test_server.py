"""Tests for yao.sdk.server — MCP server and tool functions."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from yao.sdk.server import (
    _ALL_TOOLS,
    _count_severities,
    _find_midi_in_iteration,
    _format_critique_md,
    _get_conductor,
    _project_name_from_iteration,
    _reset_conductor,
    _yao_list_iterations,
    _yao_validate_spec,
    create_yao_mcp_server,
)
from yao.sdk.tools import (
    ListIterationsInput,
    ValidateSpecInput,
)


class TestServerFactory:
    def test_create_returns_mcp_config(self) -> None:
        server = create_yao_mcp_server()
        assert server is not None
        # McpSdkServerConfig is a TypedDict with 'name' and 'type' keys
        assert server["name"] == "yao"
        assert server["type"] == "sdk"

    def test_all_tools_count(self) -> None:
        assert len(_ALL_TOOLS) == 15

    def test_tool_names_unique(self) -> None:
        names = [t.name for t in _ALL_TOOLS]
        assert len(names) == len(set(names))

    def test_all_tools_have_descriptions(self) -> None:
        for t in _ALL_TOOLS:
            assert t.description, f"Tool {t.name} missing description"


class TestConductorSingleton:
    def setup_method(self) -> None:
        _reset_conductor()

    def teardown_method(self) -> None:
        _reset_conductor()

    def test_singleton_returns_same_instance(self) -> None:
        c1 = _get_conductor()
        c2 = _get_conductor()
        assert c1 is c2

    def test_reset_clears_singleton(self) -> None:
        c1 = _get_conductor()
        _reset_conductor()
        c2 = _get_conductor()
        assert c1 is not c2


class TestHelpers:
    def test_project_name_from_iteration_path(self) -> None:
        path = Path("outputs/projects/rainy-cafe/iterations/v001")
        assert _project_name_from_iteration(path) == "rainy-cafe"

    def test_project_name_unknown_path(self) -> None:
        path = Path("/tmp/random/path")
        assert _project_name_from_iteration(path) == "unknown"

    def test_find_midi_full_mid(self, tmp_path: Path) -> None:
        (tmp_path / "full.mid").touch()
        assert _find_midi_in_iteration(tmp_path) == tmp_path / "full.mid"

    def test_find_midi_fallback(self, tmp_path: Path) -> None:
        (tmp_path / "output.mid").touch()
        assert _find_midi_in_iteration(tmp_path) == tmp_path / "output.mid"

    def test_find_midi_missing_raises(self, tmp_path: Path) -> None:
        from yao.errors import YaOError

        with pytest.raises(YaOError, match="No MIDI file"):
            _find_midi_in_iteration(tmp_path)

    def test_count_severities(self) -> None:
        issues = [
            {"severity": "critical"},
            {"severity": "major"},
            {"severity": "major"},
            {"severity": "minor"},
        ]
        counts = _count_severities(issues)
        assert counts == {"critical": 1, "major": 2, "minor": 1, "suggestion": 0}

    def test_format_critique_md(self) -> None:
        issues = [
            {
                "severity": "major",
                "category": "harmony",
                "location": "bar 4",
                "issue": "parallel fifths",
                "suggestion": "use contrary motion",
            },
        ]
        md = _format_critique_md(issues)
        assert "MAJOR" in md
        assert "parallel fifths" in md
        assert "contrary motion" in md


class TestValidateSpecTool:
    def test_valid_spec(self) -> None:
        # Use a known-good spec from the project
        specs = sorted(Path("specs/templates").rglob("composition.yaml"))
        if not specs:
            pytest.skip("No template specs found")
        args = ValidateSpecInput(spec_path=str(specs[0]))
        result = asyncio.get_event_loop().run_until_complete(_yao_validate_spec.handler(args))
        data = json.loads(result["content"][0]["text"])
        assert data["valid"] is True

    def test_invalid_spec_path(self) -> None:
        args = ValidateSpecInput(spec_path="nonexistent.yaml")
        result = asyncio.get_event_loop().run_until_complete(_yao_validate_spec.handler(args))
        data = json.loads(result["content"][0]["text"])
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestListIterationsTool:
    def test_nonexistent_project(self) -> None:
        args = ListIterationsInput(project="__nonexistent__")
        result = asyncio.get_event_loop().run_until_complete(_yao_list_iterations.handler(args))
        data = json.loads(result["content"][0]["text"])
        assert data["count"] == 0
        assert data["iterations"] == []
