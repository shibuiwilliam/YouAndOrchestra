"""Tests for yao.sdk.hooks — SDK hook callbacks."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from yao.sdk.hooks import (
    default_yao_hooks,
    post_iteration_provenance,
    pre_compose_validate,
)

_CTX: dict[str, object] = {"signal": None}


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.get_event_loop().run_until_complete(coro)


class TestDefaultHooks:
    def test_returns_dict_with_pre_and_post(self) -> None:
        hooks = default_yao_hooks()
        assert "PreToolUse" in hooks
        assert "PostToolUse" in hooks

    def test_pre_tool_use_has_matchers(self) -> None:
        hooks = default_yao_hooks()
        assert len(hooks["PreToolUse"]) >= 1

    def test_post_tool_use_has_matchers(self) -> None:
        hooks = default_yao_hooks()
        assert len(hooks["PostToolUse"]) >= 2


class TestPostIterationProvenance:
    def test_appends_provenance_for_compose(self, tmp_path: Path) -> None:
        iter_dir = tmp_path / "iterations" / "v001"
        iter_dir.mkdir(parents=True)
        prov_path = iter_dir / "provenance.json"
        prov_path.write_text("[]")

        input_data = {
            "tool_name": "mcp__yao__yao_compose",
            "tool_response": {"iteration_path": str(iter_dir)},
        }
        _run(post_iteration_provenance(input_data, "test-session", _CTX))  # type: ignore[arg-type]

        records = json.loads(prov_path.read_text())
        assert len(records) > 0
        assert records[-1]["operation"] == "post_tool_provenance"

    def test_ignores_non_mutating_tools(self) -> None:
        input_data = {
            "tool_name": "mcp__yao__yao_evaluate",
            "tool_response": {},
        }
        result = _run(post_iteration_provenance(input_data, None, _CTX))  # type: ignore[arg-type]
        assert result == {}


class TestPreComposeValidate:
    def test_allows_valid_spec(self, tmp_path: Path) -> None:
        spec_path = tmp_path / "composition.yaml"
        spec_path.write_text(
            'title: "Test"\n'
            'genre: "general"\n'
            'key: "C major"\n'
            "tempo_bpm: 120\n"
            'time_signature: "4/4"\n'
            "total_bars: 8\n"
            "instruments:\n"
            "  - name: piano\n"
            "    role: melody\n"
            "sections:\n"
            "  - name: verse\n"
            "    bars: 8\n"
            '    dynamics: "mf"\n'
        )

        input_data = {"tool_input": {"spec_path": str(spec_path)}}
        result = _run(pre_compose_validate(input_data, None, _CTX))  # type: ignore[arg-type]
        hook_output = result.get("hookSpecificOutput", {})
        assert hook_output.get("permissionDecision") != "deny"

    def test_denies_invalid_spec(self, tmp_path: Path) -> None:
        spec_path = tmp_path / "bad.yaml"
        spec_path.write_text("not_a_valid_spec: true\n")

        input_data = {"tool_input": {"spec_path": str(spec_path)}}
        result = _run(pre_compose_validate(input_data, None, _CTX))  # type: ignore[arg-type]
        hook_output = result.get("hookSpecificOutput", {})
        assert hook_output.get("permissionDecision") == "deny"

    def test_allows_nonexistent_spec(self) -> None:
        input_data = {"tool_input": {"spec_path": "nonexistent.yaml"}}
        result = _run(pre_compose_validate(input_data, None, _CTX))  # type: ignore[arg-type]
        hook_output = result.get("hookSpecificOutput", {})
        assert hook_output.get("permissionDecision") != "deny"

    def test_allows_description_input(self) -> None:
        input_data = {"tool_input": {"spec_or_desc": "a calm piano piece"}}
        result = _run(pre_compose_validate(input_data, None, _CTX))  # type: ignore[arg-type]
        assert result == {}
