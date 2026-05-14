"""SDK hooks — guaranteed auto-render, auto-critique, auto-provenance.

Hooks make non-negotiable behaviors infrastructure rather than discipline.
They run regardless of agent forgetfulness, enforcing the four standard
YaO guarantees from PROJECT.md §10.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_agent_sdk import HookCallback, HookMatcher
from claude_agent_sdk.types import (
    HookContext,
    HookInput,
)

from yao.reflect.provenance import ProvenanceLog

# Tool names that mutate iterations
_ITERATION_MUTATING_TOOLS = frozenset(
    {
        "mcp__yao__yao_compose",
        "mcp__yao__yao_conduct",
        "mcp__yao__yao_regenerate_section",
    }
)

# Tool names that trigger compose hooks
_COMPOSE_TOOLS = frozenset(
    {
        "mcp__yao__yao_compose",
        "mcp__yao__yao_conduct",
    }
)


def _soundfont_available() -> bool:
    """Check if a SoundFont file is available for audio rendering."""
    sf_paths = [
        Path("soundfonts/FluidR3_GM.sf2"),
        Path("soundfonts/default.sf2"),
    ]
    return any(p.exists() for p in sf_paths)


def _find_soundfont() -> Path | None:
    """Find the first available SoundFont."""
    for p in [Path("soundfonts/FluidR3_GM.sf2"), Path("soundfonts/default.sf2")]:
        if p.exists():
            return p
    return None


async def post_iteration_provenance(
    input_data: HookInput,
    session_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """After any tool that mutates an iteration: append a provenance event."""
    tool_name = input_data.get("tool_name", "")
    if tool_name in _ITERATION_MUTATING_TOOLS:
        tool_response = input_data.get("tool_response", {})
        if isinstance(tool_response, dict):
            iteration_path = tool_response.get("iteration_path") or tool_response.get("final_iteration")
            if iteration_path:
                prov_path = Path(str(iteration_path)) / "provenance.json"
                log = ProvenanceLog()
                log.record(
                    layer="sdk",
                    operation="post_tool_provenance",
                    parameters={"tool": tool_name, "session_id": session_id or ""},
                    source="sdk_hook",
                    rationale="Automatic provenance recording via SDK hook",
                )
                log.save(prov_path)
    return {}


async def post_compose_render(
    input_data: HookInput,
    session_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """After yao_compose / yao_conduct: render audio if SoundFont is available."""
    tool_name = input_data.get("tool_name", "")
    if tool_name in _COMPOSE_TOOLS and _soundfont_available():
        tool_response = input_data.get("tool_response", {})
        if isinstance(tool_response, dict):
            midi_path_str = tool_response.get("midi_path")
            if midi_path_str:
                midi_path = Path(str(midi_path_str))
                if midi_path.exists():
                    sf = _find_soundfont()
                    if sf:
                        try:
                            from yao.render.audio_renderer import render_midi_to_wav

                            wav_path = midi_path.with_suffix(".wav")
                            render_midi_to_wav(midi_path, wav_path, soundfont_path=sf)
                        except Exception:
                            pass  # Best-effort
    return {}


async def post_compose_critique(
    input_data: HookInput,
    session_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """After yao_compose: auto-run the Adversarial Critic."""
    tool_name = input_data.get("tool_name", "")
    if tool_name == "mcp__yao__yao_compose":
        tool_response = input_data.get("tool_response", {})
        if isinstance(tool_response, dict):
            iteration_path = tool_response.get("iteration_path")
            if iteration_path:
                iter_path = Path(str(iteration_path))
                midi_path = iter_path / "full.mid"
                if midi_path.exists():
                    try:
                        from yao.render.midi_reader import load_midi_to_score_ir
                        from yao.verify.analyzer import analyze_score

                        score_ir = load_midi_to_score_ir(midi_path)
                        analysis = analyze_score(score_ir)

                        issues = []
                        for lr in analysis.lint_results:
                            issues.append(f"- [{lr.severity}] {lr.message} ({lr.location})")

                        if issues:
                            critique_md = "# Auto-Critique (SDK Hook)\n\n" + "\n".join(issues) + "\n"
                            (iter_path / "critique.md").write_text(critique_md)
                    except Exception:
                        pass  # Best-effort
    return {}


async def pre_compose_validate(
    input_data: HookInput,
    session_id: str | None,
    context: HookContext,
) -> dict[str, Any]:
    """Before yao_compose / yao_conduct: validate the spec.

    Blocks the call with a deny decision if the spec is invalid.
    """
    tool_input = input_data.get("tool_input", {})
    if isinstance(tool_input, dict):
        spec_path_str = tool_input.get("spec_path") or tool_input.get("spec_or_desc")
        if spec_path_str and isinstance(spec_path_str, str):
            spec_path = Path(spec_path_str)
            if spec_path.suffix in {".yaml", ".yml"} and spec_path.exists():
                try:
                    from yao.schema.loader import load_composition_spec_auto

                    load_composition_spec_auto(spec_path)
                except Exception as exc:
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": (
                                f"Spec failed validation: {exc}. Run yao_validate_spec first."
                            ),
                        }
                    }
    return {}


def default_yao_hooks() -> dict[str, list[HookMatcher]]:
    """Return the four standard YaO hooks for SDK sessions.

    Returns:
        Hook configuration dict for ``ClaudeAgentOptions.hooks``.
    """
    # Cast to HookCallback to satisfy mypy — our functions match the
    # HookCallback protocol but return dict[str, Any] rather than
    # the exact TypedDict union.
    pre_validate: HookCallback = pre_compose_validate  # type: ignore[assignment]
    post_prov: HookCallback = post_iteration_provenance  # type: ignore[assignment]
    post_render: HookCallback = post_compose_render  # type: ignore[assignment]
    post_critique: HookCallback = post_compose_critique  # type: ignore[assignment]

    return {
        "PreToolUse": [
            HookMatcher(
                matcher="mcp__yao__yao_compose|mcp__yao__yao_conduct",
                hooks=[pre_validate],
            ),
        ],
        "PostToolUse": [
            HookMatcher(
                matcher="mcp__yao__.*",
                hooks=[post_prov],
            ),
            HookMatcher(
                matcher="mcp__yao__yao_compose|mcp__yao__yao_conduct",
                hooks=[post_render, post_critique],
            ),
        ],
    }
