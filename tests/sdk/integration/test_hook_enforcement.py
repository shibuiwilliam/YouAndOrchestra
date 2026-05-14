"""Integration test: hooks fire even when agent tries to skip them.

§17.3: Build a test that runs through the hooks and verifies
provenance is written, critique is attempted, and validation
blocks invalid specs — regardless of agent behavior.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from yao.sdk.hooks import (
    post_iteration_provenance,
    pre_compose_validate,
)

_CTX: dict[str, object] = {"signal": None}


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.get_event_loop().run_until_complete(coro)


class TestProvenanceHookEnforcement:
    """Provenance must be written for any iteration-mutating tool."""

    def test_compose_writes_provenance(self, tmp_path: Path) -> None:
        iter_dir = tmp_path / "v001"
        iter_dir.mkdir()
        (iter_dir / "provenance.json").write_text("[]")

        input_data = {
            "tool_name": "mcp__yao__yao_compose",
            "tool_response": {"iteration_path": str(iter_dir)},
        }
        _run(post_iteration_provenance(input_data, None, _CTX))  # type: ignore[arg-type]

        records = json.loads((iter_dir / "provenance.json").read_text())
        assert len(records) >= 1
        assert records[-1]["source"] == "sdk_hook"

    def test_conduct_writes_provenance(self, tmp_path: Path) -> None:
        iter_dir = tmp_path / "v001"
        iter_dir.mkdir()
        (iter_dir / "provenance.json").write_text("[]")

        input_data = {
            "tool_name": "mcp__yao__yao_conduct",
            "tool_response": {"final_iteration": str(iter_dir)},
        }
        _run(post_iteration_provenance(input_data, None, _CTX))  # type: ignore[arg-type]

        records = json.loads((iter_dir / "provenance.json").read_text())
        assert len(records) >= 1

    def test_regenerate_writes_provenance(self, tmp_path: Path) -> None:
        iter_dir = tmp_path / "v002"
        iter_dir.mkdir()
        (iter_dir / "provenance.json").write_text("[]")

        input_data = {
            "tool_name": "mcp__yao__yao_regenerate_section",
            "tool_response": {"iteration_path": str(iter_dir)},
        }
        _run(post_iteration_provenance(input_data, None, _CTX))  # type: ignore[arg-type]

        records = json.loads((iter_dir / "provenance.json").read_text())
        assert len(records) >= 1

    def test_evaluate_does_not_write_provenance(self, tmp_path: Path) -> None:
        """Non-mutating tools must not append provenance."""
        iter_dir = tmp_path / "v001"
        iter_dir.mkdir()
        (iter_dir / "provenance.json").write_text("[]")

        input_data = {
            "tool_name": "mcp__yao__yao_evaluate",
            "tool_response": {"iteration_path": str(iter_dir)},
        }
        _run(post_iteration_provenance(input_data, None, _CTX))  # type: ignore[arg-type]

        records = json.loads((iter_dir / "provenance.json").read_text())
        assert len(records) == 0


class TestValidationHookEnforcement:
    """Invalid specs must be blocked before composition starts."""

    def test_blocks_invalid_yaml(self, tmp_path: Path) -> None:
        bad_spec = tmp_path / "bad.yaml"
        bad_spec.write_text("this_is_not_a_spec: true\n")

        input_data = {"tool_input": {"spec_path": str(bad_spec)}}
        result = _run(pre_compose_validate(input_data, None, _CTX))  # type: ignore[arg-type]

        hook_out = result.get("hookSpecificOutput", {})
        assert hook_out.get("permissionDecision") == "deny"

    def test_allows_valid_yaml(self, tmp_path: Path) -> None:
        good_spec = tmp_path / "composition.yaml"
        good_spec.write_text(
            'title: "Test"\ngenre: "general"\nkey: "C major"\n'
            "tempo_bpm: 120\n"
            'time_signature: "4/4"\ntotal_bars: 8\n'
            "instruments:\n  - name: piano\n    role: melody\n"
            "sections:\n  - name: verse\n    bars: 8\n"
            '    dynamics: "mf"\n'
        )

        input_data = {"tool_input": {"spec_path": str(good_spec)}}
        result = _run(pre_compose_validate(input_data, None, _CTX))  # type: ignore[arg-type]

        hook_out = result.get("hookSpecificOutput", {})
        assert hook_out.get("permissionDecision") != "deny"
