"""In-process MCP server — exposes YaO engine capabilities as SDK tools.

The server wraps every major Conductor and engine operation as an MCP tool,
enabling agents to compose, critique, render, and evaluate music without
subprocess overhead.

All tools share a single Conductor instance in the process, so provenance,
caches, and ScoreIR are naturally shared across calls.

Belongs to the SDK Surface layer (above Layer 7).
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import structlog
from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server, tool
from mcp.types import ToolAnnotations

from yao.conductor.conductor import Conductor
from yao.errors import YaOError
from yao.render.audio_renderer import render_midi_to_wav
from yao.render.iteration import list_iterations
from yao.render.midi_reader import load_midi_to_score_ir
from yao.schema.composition_v2 import CompositionSpecV2
from yao.schema.loader import (
    load_composition_spec_auto,
    load_project_specs,
)
from yao.sdk.tools import (
    ArchLintInput,
    ComposeInput,
    ConductInput,
    CritiqueInput,
    DiffInput,
    EvaluateInput,
    ExplainInput,
    ListIterationsInput,
    LoadSpecInput,
    NewProjectInput,
    ReadIterationInput,
    RegenerateSectionInput,
    RenderAudioInput,
    RunTestsInput,
    ValidateSpecInput,
)
from yao.verify.diff import diff_scores
from yao.verify.evaluator import evaluate_score

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Conductor singleton
# ---------------------------------------------------------------------------

_conductor: Conductor | None = None


def _get_conductor() -> Conductor:
    """Return the process-wide Conductor singleton."""
    global _conductor
    if _conductor is None:
        _conductor = Conductor()
    return _conductor


def _reset_conductor() -> None:
    """Reset the Conductor singleton (for testing only)."""
    global _conductor
    _conductor = None


# ---------------------------------------------------------------------------
# Helper: wrap tool handlers with YaOError → MCP error translation
# ---------------------------------------------------------------------------


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    """Build a successful MCP tool result."""
    return {"content": [{"type": "text", "text": json.dumps(data, default=str)}]}


def _err(exc: Exception) -> dict[str, Any]:
    """Build an MCP error result with structured payload when possible.

    For domain-specific errors (RangeViolationError, SpecValidationError),
    includes structured fields so the agent can reason about the fix
    (§6.4: "the violin can't play that low — let me transpose up").
    """
    from yao.errors import RangeViolationError, SpecValidationError

    error_data: dict[str, Any] = {"error_type": type(exc).__name__, "message": str(exc)}

    if isinstance(exc, RangeViolationError):
        error_data["instrument"] = exc.instrument
        error_data["note"] = exc.note
        error_data["valid_low"] = exc.valid_low
        error_data["valid_high"] = exc.valid_high
    elif isinstance(exc, SpecValidationError):
        error_data["field"] = exc.field

    return {
        "content": [{"type": "text", "text": json.dumps(error_data, default=str)}],
        "isError": True,
    }


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


@tool(
    "yao_compose",
    "Generate a single MIDI iteration from a YAML spec without auto-iteration.",
    ComposeInput,
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def _yao_compose(args: ComposeInput) -> dict[str, Any]:
    try:
        spec_path = Path(args.spec_path)
        raw_spec = load_composition_spec_auto(spec_path)
        spec = raw_spec.to_v1() if isinstance(raw_spec, CompositionSpecV2) else raw_spec
        conductor = _get_conductor()
        result = await asyncio.to_thread(conductor.compose_from_spec, spec, max_iterations=1)
        return _ok(
            {
                "iteration_path": str(result.output_dir),
                "midi_path": str(result.midi_path),
                "evaluation": {
                    "pass_rate": result.evaluation.pass_rate,
                    "quality_score": result.evaluation.quality_score,
                    "passed": result.evaluation.passed,
                },
                "provenance_entries": len(result.provenance.records),
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_conduct",
    "Run the full generate-evaluate-adapt-regenerate loop. Accepts a YAML spec path or a natural-language description.",
    ConductInput,
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def _yao_conduct(args: ConductInput) -> dict[str, Any]:
    try:
        conductor = _get_conductor()
        if args.is_description:
            result = await asyncio.to_thread(
                conductor.compose_from_description,
                args.spec_or_desc,
                max_iterations=args.max_iterations,
            )
        else:
            raw_spec = load_composition_spec_auto(Path(args.spec_or_desc))
            spec = raw_spec.to_v1() if isinstance(raw_spec, CompositionSpecV2) else raw_spec
            result = await asyncio.to_thread(
                conductor.compose_from_spec,
                spec,
                max_iterations=args.max_iterations,
            )
        return _ok(
            {
                "final_iteration": str(result.output_dir),
                "midi_path": str(result.midi_path),
                "iterations": result.iterations,
                "pass_rate": result.evaluation.pass_rate,
                "quality_score": result.evaluation.quality_score,
                "adaptations_applied": result.adaptations_applied,
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_critique",
    "Run the Adversarial Critic on an iteration to find weaknesses.",
    CritiqueInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_critique(args: CritiqueInput) -> dict[str, Any]:
    try:
        from yao.verify.analyzer import analyze_score

        iter_path = Path(args.iteration_path)
        midi_path = _find_midi_in_iteration(iter_path)
        score_ir = load_midi_to_score_ir(midi_path)
        analysis = analyze_score(score_ir)

        # Build critique issues from analysis lint results
        issues: list[dict[str, Any]] = []
        for lint_result in analysis.lint_results:
            sev = "major" if lint_result.severity == "error" else "minor"
            issues.append(
                {
                    "severity": sev,
                    "category": "analysis",
                    "issue": lint_result.message,
                    "location": lint_result.location,
                    "suggestion": None,
                }
            )

        # Check for common problems
        if analysis.total_notes == 0:
            issues.append(
                {
                    "severity": "critical",
                    "category": "structure",
                    "issue": "Score contains no notes",
                    "location": "global",
                    "suggestion": "Verify the generation pipeline produced output",
                }
            )

        critique_md = _format_critique_md(issues)
        critique_path = iter_path / "critique.md"
        critique_path.write_text(critique_md)

        return _ok(
            {
                "critique_md_path": str(critique_path),
                "issues": issues,
                "severity_counts": _count_severities(issues),
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_regenerate_section",
    "Regenerate a specific section of a composition while preserving the rest.",
    RegenerateSectionInput,
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def _yao_regenerate_section(args: RegenerateSectionInput) -> dict[str, Any]:
    try:
        project_dir = Path(f"specs/projects/{args.project}")
        spec, trajectory = load_project_specs(project_dir)
        v1_spec = spec.to_v1() if isinstance(spec, CompositionSpecV2) else spec

        # Find the latest iteration to regenerate from
        output_dir = Path(f"outputs/projects/{args.project}")
        iterations = list_iterations(output_dir)
        if not iterations:
            return _err(YaOError(f"No iterations found for project '{args.project}'"))

        latest = iterations[-1]
        midi_path = _find_midi_in_iteration(latest)
        current_score = load_midi_to_score_ir(midi_path)

        conductor = _get_conductor()
        result = await asyncio.to_thread(
            conductor.regenerate_section,
            current_score,
            v1_spec,
            args.section,
            trajectory=trajectory,
            project_name=args.project,
            seed_override=args.seed,
        )
        return _ok(
            {
                "new_iteration_path": str(result.output_dir),
                "midi_path": str(result.midi_path),
                "section_regenerated": args.section,
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_render_audio",
    "Render a MIDI file to WAV audio using FluidSynth.",
    RenderAudioInput,
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def _yao_render_audio(args: RenderAudioInput) -> dict[str, Any]:
    try:
        midi_path = Path(args.midi_path)
        wav_path = midi_path.with_suffix(".wav")
        sf_path = Path(args.soundfont) if args.soundfont else None

        result = await asyncio.to_thread(render_midi_to_wav, midi_path, wav_path, soundfont_path=sf_path)
        return _ok(
            {
                "wav_path": str(result.output_path),
                "duration_seconds": result.duration_seconds,
                "sample_rate": result.sample_rate,
            }
        )
    except (YaOError, Exception) as exc:
        return _err(exc)


@tool(
    "yao_evaluate",
    "Run quality evaluation on a composition iteration.",
    EvaluateInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_evaluate(args: EvaluateInput) -> dict[str, Any]:
    try:
        iter_path = Path(args.iteration_path)
        midi_path = _find_midi_in_iteration(iter_path)
        score_ir = load_midi_to_score_ir(midi_path)

        # Try to find the spec for this project
        project_name = _project_name_from_iteration(iter_path)
        spec_dir = Path(f"specs/projects/{project_name}")
        spec: CompositionSpec | None = None
        if spec_dir.exists():
            raw_spec, _trajectory = load_project_specs(spec_dir)
            spec = raw_spec.to_v1() if isinstance(raw_spec, CompositionSpecV2) else raw_spec

        if spec is None:
            # Build a minimal spec from the score IR for evaluation
            from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec

            spec = CompositionSpec(
                title=score_ir.title,
                key=score_ir.key,
                tempo_bpm=score_ir.tempo_bpm,
                time_signature=score_ir.time_signature,
                instruments=[InstrumentSpec(name=name, role="melody") for name in score_ir.instruments()],
                sections=[SectionSpec(name=s.name, bars=s.bar_count) for s in score_ir.sections],
            )

        report = evaluate_score(score_ir, spec)
        eval_path = iter_path / "evaluation.json"
        eval_path.write_text(report.to_json())

        return _ok(
            {
                "evaluation_json_path": str(eval_path),
                "pass_rate": report.pass_rate,
                "quality_score": report.quality_score,
                "passed": report.passed,
                "scores": {s.metric: s.score for s in report.scores},
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_diff",
    "Compare two iterations and show musical differences.",
    DiffInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_diff(args: DiffInput) -> dict[str, Any]:
    try:
        midi_a = _find_midi_in_iteration(Path(args.iter_a))
        midi_b = _find_midi_in_iteration(Path(args.iter_b))
        score_a = load_midi_to_score_ir(midi_a)
        score_b = load_midi_to_score_ir(midi_b)

        result = diff_scores(score_a, score_b)
        return _ok(
            {
                "summary": f"{result.total_changes} note changes between '{result.title_a}' and '{result.title_b}'",
                "added": len(result.added_notes),
                "removed": len(result.removed_notes),
                "modified": len(result.modified_notes),
                "section_changes": result.section_changes,
                "tempo_changed": result.tempo_changed,
                "key_changed": result.key_changed,
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_explain",
    "Query the provenance log to explain a generation decision.",
    ExplainInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_explain(args: ExplainInput) -> dict[str, Any]:
    try:
        if args.iteration_path:
            prov_path = Path(args.iteration_path) / "provenance.json"
            if prov_path.exists():
                records: list[dict[str, Any]] = json.loads(prov_path.read_text())
                query_lower = args.query.lower()
                matching = [
                    r
                    for r in records
                    if query_lower in r.get("operation", "").lower() or query_lower in r.get("rationale", "").lower()
                ]
                return _ok({"query": args.query, "chain": matching})

        return _ok({"query": args.query, "chain": [], "note": "No matching provenance records"})
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_validate_spec",
    "Validate a YAML composition spec against the Pydantic schema.",
    ValidateSpecInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_validate_spec(args: ValidateSpecInput) -> dict[str, Any]:
    try:
        load_composition_spec_auto(Path(args.spec_path))
        return _ok({"valid": True, "errors": []})
    except Exception as exc:
        return _ok({"valid": False, "errors": [str(exc)]})


@tool(
    "yao_load_spec",
    "Load and parse a YAML composition spec, returning its contents.",
    LoadSpecInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_load_spec(args: LoadSpecInput) -> dict[str, Any]:
    try:
        spec = load_composition_spec_auto(Path(args.spec_path))
        return _ok({"spec": spec.model_dump()})
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_new_project",
    "Create a new YaO project with default template files.",
    NewProjectInput,
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
async def _yao_new_project(args: NewProjectInput) -> dict[str, Any]:
    try:
        import shutil

        project_dir = Path(f"specs/projects/{args.name}")
        if project_dir.exists():
            return _err(YaOError(f"Project '{args.name}' already exists"))

        if args.from_template:
            template_dir = Path(f"specs/templates/{args.from_template}")
            if not template_dir.exists():
                return _err(YaOError(f"Template '{args.from_template}' not found"))
            shutil.copytree(template_dir, project_dir)
        else:
            project_dir.mkdir(parents=True, exist_ok=True)
            # Find any template to copy
            templates_dir = Path("specs/templates")
            if templates_dir.exists():
                templates = sorted(templates_dir.iterdir())
                if templates:
                    for item in templates[0].iterdir():
                        if item.is_file():
                            shutil.copy2(item, project_dir / item.name)

        # Also create outputs directory
        output_dir = Path(f"outputs/projects/{args.name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        return _ok({"project_path": str(project_dir)})
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_list_iterations",
    "List all iterations for a project.",
    ListIterationsInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_list_iterations(args: ListIterationsInput) -> dict[str, Any]:
    output_dir = Path(f"outputs/projects/{args.project}")
    iterations = list_iterations(output_dir) if output_dir.exists() else []
    return _ok(
        {
            "iterations": [str(p) for p in iterations],
            "count": len(iterations),
        }
    )


@tool(
    "yao_read_iteration",
    "Read details of a specific iteration including MIDI info and analysis.",
    ReadIterationInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_read_iteration(args: ReadIterationInput) -> dict[str, Any]:
    try:
        iter_path = Path(f"outputs/projects/{args.project}/iterations/{args.iteration}")
        if not iter_path.exists():
            return _err(YaOError(f"Iteration '{args.iteration}' not found for project '{args.project}'"))

        midi_path = _find_midi_in_iteration(iter_path)
        score_ir = load_midi_to_score_ir(midi_path)

        stems = sorted(str(p) for p in iter_path.glob("stems/*.mid"))
        eval_path = iter_path / "evaluation.json"
        evaluation = json.loads(eval_path.read_text()) if eval_path.exists() else None

        return _ok(
            {
                "midi_path": str(midi_path),
                "stems": stems,
                "title": score_ir.title,
                "duration_seconds": score_ir.duration_seconds(),
                "total_bars": score_ir.total_bars(),
                "instruments": score_ir.instruments(),
                "note_count": len(score_ir.all_notes()),
                "evaluation": evaluation,
            }
        )
    except YaOError as exc:
        return _err(exc)


@tool(
    "yao_arch_lint",
    "Run the architecture lint to check layer-boundary compliance.",
    ArchLintInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_arch_lint(args: ArchLintInput) -> dict[str, Any]:
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "tools/architecture_lint.py"],
        capture_output=True,
        text=True,
    )
    return _ok(
        {
            "violations": [] if result.returncode == 0 else result.stdout.strip().split("\n"),
            "exit_code": result.returncode,
            "output": result.stdout.strip(),
        }
    )


@tool(
    "yao_run_tests",
    "Run the YaO test suite (or a subset).",
    RunTestsInput,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def _yao_run_tests(args: RunTestsInput) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "-q"]
    if args.target:
        cmd.append(args.target)

    result = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
    )

    # Parse pytest output for pass/fail counts
    output = result.stdout.strip()
    return _ok(
        {
            "exit_code": result.returncode,
            "output": output,
            "passed": output.count(" passed"),
            "failed": output.count(" failed"),
        }
    )


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------

# Collect all tool objects for the server
_ALL_TOOLS: list[SdkMcpTool[Any]] = [
    _yao_compose,
    _yao_conduct,
    _yao_critique,
    _yao_regenerate_section,
    _yao_render_audio,
    _yao_evaluate,
    _yao_diff,
    _yao_explain,
    _yao_validate_spec,
    _yao_load_spec,
    _yao_new_project,
    _yao_list_iterations,
    _yao_read_iteration,
    _yao_arch_lint,
    _yao_run_tests,
]


def create_yao_mcp_server() -> Any:
    """Create the in-process MCP server with all YaO music tools.

    Returns an ``McpSdkServerConfig`` ready to plug into
    ``ClaudeAgentOptions.mcp_servers``.

    Returns:
        An McpSdkServerConfig instance.
    """
    return create_sdk_mcp_server(
        name="yao",
        version="1.0.0",
        tools=_ALL_TOOLS,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_midi_in_iteration(iter_path: Path) -> Path:
    """Find the main MIDI file in an iteration directory.

    Looks for full.mid first, then any .mid file.

    Args:
        iter_path: Path to the iteration directory.

    Returns:
        Path to the MIDI file.

    Raises:
        YaOError: If no MIDI file is found.
    """
    full_mid = iter_path / "full.mid"
    if full_mid.exists():
        return full_mid

    midi_files = sorted(iter_path.glob("*.mid"))
    if midi_files:
        return midi_files[0]

    raise YaOError(f"No MIDI file found in {iter_path}")


def _project_name_from_iteration(iter_path: Path) -> str:
    """Extract the project name from an iteration path.

    Expects paths like outputs/projects/<name>/iterations/v001.

    Args:
        iter_path: Path to an iteration directory.

    Returns:
        The project name.
    """
    parts = iter_path.parts
    try:
        idx = parts.index("projects")
        return parts[idx + 1]
    except (ValueError, IndexError):
        return "unknown"


def _format_critique_md(issues: list[dict[str, Any]]) -> str:
    """Format critique issues as Markdown.

    Args:
        issues: List of issue dicts with severity, category, issue, etc.

    Returns:
        Markdown string.
    """
    lines = ["# Adversarial Critique\n"]
    for sev in ("critical", "major", "minor", "suggestion"):
        sev_issues = [i for i in issues if i.get("severity") == sev]
        if sev_issues:
            lines.append(f"\n## {sev.upper()} ({len(sev_issues)})\n")
            for issue in sev_issues:
                lines.append(
                    f"- **{issue.get('category', 'general')}** "
                    f"({issue.get('location', 'unknown')}): "
                    f"{issue.get('issue', '')}"
                )
                if issue.get("suggestion"):
                    lines.append(f"  - *Suggestion:* {issue['suggestion']}")
    return "\n".join(lines) + "\n"


def _count_severities(issues: list[dict[str, Any]]) -> dict[str, int]:
    """Count issues by severity level.

    Args:
        issues: List of issue dicts.

    Returns:
        Dict mapping severity to count.
    """
    counts: dict[str, int] = {"critical": 0, "major": 0, "minor": 0, "suggestion": 0}
    for issue in issues:
        sev = issue.get("severity", "minor")
        counts[sev] = counts.get(sev, 0) + 1
    return counts
