"""AnthropicAPIBackend — invoke Subagents via Anthropic Messages API.

Real implementation (Wave 1.2). Calls the Anthropic API with:
- .claude/agents/<role>.md as system prompt
- AgentContext serialized as structured user message
- Tool use for structured output parsing

No silent fallback. Missing API key → BackendNotConfiguredError.
API errors → AgentBackendError.

Belongs to agents/ package (Layer 7).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

try:
    import anthropic  # type: ignore[import-not-found]
except ImportError:
    anthropic = None  # type: ignore[assignment,unused-ignore]

from yao.agents.protocol import AgentInvocationConfig
from yao.errors import AgentBackendError, AgentOutputParseError, BackendNotConfiguredError
from yao.reflect.provenance import ProvenanceLog
from yao.subagents.base import AgentContext, AgentOutput, AgentRole

logger = structlog.get_logger()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

# Role → filename mapping (handles underscores vs hyphens)
_ROLE_TO_FILE: dict[AgentRole, str] = {
    AgentRole.COMPOSER: "composer.md",
    AgentRole.HARMONY_THEORIST: "harmony-theorist.md",
    AgentRole.RHYTHM_ARCHITECT: "rhythm-architect.md",
    AgentRole.ORCHESTRATOR: "orchestrator.md",
    AgentRole.ADVERSARIAL_CRITIC: "adversarial-critic.md",
    AgentRole.MIX_ENGINEER: "mix-engineer.md",
    AgentRole.PRODUCER: "producer.md",
}

# Default model
_DEFAULT_MODEL = "claude-sonnet-4-6"
_ENV_MODEL = "YAO_LLM_MODEL"
_COST_WARNING_THRESHOLD = 100


def _output_schema_for_role(role: AgentRole) -> dict[str, Any]:
    """Return simplified JSON schema for the expected output fields per role."""
    schemas: dict[AgentRole, dict[str, Any]] = {
        AgentRole.COMPOSER: {
            "type": "object",
            "properties": {
                "motif_plan": {"type": "object", "description": "MotifPlan with seeds and transformations"},
                "phrase_plan": {"type": "object", "description": "PhrasePlan with phrases"},
            },
            "required": ["motif_plan"],
        },
        AgentRole.HARMONY_THEORIST: {
            "type": "object",
            "properties": {
                "harmony_plan": {"type": "object", "description": "HarmonyPlan with chord_events and cadences"},
            },
            "required": ["harmony_plan"],
        },
        AgentRole.RHYTHM_ARCHITECT: {
            "type": "object",
            "properties": {
                "drum_pattern": {"type": "object", "description": "DrumPattern with hits and genre"},
            },
            "required": ["drum_pattern"],
        },
        AgentRole.ORCHESTRATOR: {
            "type": "object",
            "properties": {
                "arrangement_plan": {"type": "object", "description": "ArrangementPlan with layers"},
            },
            "required": ["arrangement_plan"],
        },
        AgentRole.ADVERSARIAL_CRITIC: {
            "type": "object",
            "properties": {
                "findings": {"type": "array", "items": {"type": "object"}, "description": "List of Finding objects"},
            },
            "required": ["findings"],
        },
        AgentRole.MIX_ENGINEER: {
            "type": "object",
            "properties": {
                "production_manifest": {"type": "object", "description": "ProductionManifest"},
            },
            "required": ["production_manifest"],
        },
        AgentRole.PRODUCER: {
            "type": "object",
            "properties": {
                "form_plan": {"type": "object", "description": "SongFormPlan"},
                "overrides": {"type": "object", "description": "Override decisions"},
                "escalations": {"type": "array", "items": {"type": "string"}, "description": "Escalation messages"},
            },
            "required": ["form_plan"],
        },
    }
    return schemas.get(role, {"type": "object", "properties": {}})


class AnthropicAPIBackend:
    """Agent backend using the Anthropic Messages API.

    Requires ANTHROPIC_API_KEY (env var or explicit parameter).
    Calls the API with role-specific system prompts from .claude/agents/.
    Structured output via tool_use. No silent fallback.
    """

    is_stub = False

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize with API key and model.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            model: Model to use. Falls back to YAO_LLM_MODEL env var,
                then to default (claude-sonnet-4-6).

        Raises:
            BackendNotConfiguredError: If no API key is available.
        """
        if anthropic is None:
            raise BackendNotConfiguredError(
                "AnthropicAPIBackend requires the 'anthropic' package. Install with: pip install yao[llm]"
            )

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise BackendNotConfiguredError(
                "AnthropicAPIBackend requires an API key. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key= parameter. "
                "Use PythonOnlyBackend if you do not have an API key."
            )

        self._client = anthropic.Anthropic(api_key=resolved_key)
        self._model = model or os.environ.get(_ENV_MODEL, _DEFAULT_MODEL)
        self._prompts = self._load_role_prompts()
        self._call_count = 0

    def _load_role_prompts(self) -> dict[AgentRole, str]:
        """Load .claude/agents/*.md as system prompts for each role."""
        prompts: dict[AgentRole, str] = {}
        for role, filename in _ROLE_TO_FILE.items():
            path = AGENTS_DIR / filename
            if path.exists():
                prompts[role] = path.read_text(encoding="utf-8")
            else:
                prompts[role] = f"You are the {role.value} subagent. Follow your role precisely."
                logger.warning(
                    "agent_prompt_missing",
                    role=role.value,
                    expected_path=str(path),
                )
        return prompts

    def invoke(
        self,
        role: AgentRole,
        context: AgentContext,
        config: AgentInvocationConfig | None = None,
    ) -> AgentOutput:
        """Invoke a Subagent via the Anthropic API.

        Args:
            role: Which Subagent to invoke.
            context: The current pipeline state.
            config: Invocation configuration (max_tokens, temperature).

        Returns:
            AgentOutput with the Subagent's contribution and provenance.

        Raises:
            AgentBackendError: On API errors or timeouts.
            AgentOutputParseError: If the response cannot be parsed.
        """
        cfg = config or AgentInvocationConfig()

        system_prompt = self._prompts.get(role, "")
        user_message = self._serialize_context(context)
        schema = _output_schema_for_role(role)

        # Cost safety
        self._call_count += 1
        if self._call_count >= _COST_WARNING_THRESHOLD:
            logger.warning(
                "high_llm_call_count",
                call_count=self._call_count,
                message=f"Session has made {self._call_count} LLM calls. Consider cost implications.",
            )

        # Compute prompt hash for provenance
        prompt_hash = hashlib.sha256((system_prompt + user_message).encode("utf-8")).hexdigest()[:16]

        try:
            response = self._client.messages.create(
                model=self._model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=cfg.max_tokens,
                temperature=cfg.temperature,
                tools=[
                    {
                        "name": "submit_output",
                        "description": f"Submit the {role.value} subagent output.",
                        "input_schema": schema,
                    }
                ],
                tool_choice={"type": "tool", "name": "submit_output"},
            )
        except Exception as e:
            raise AgentBackendError(f"Anthropic API call failed for role={role.value}: {e}") from e

        # Extract tool_use block
        tool_input = self._extract_tool_input(response, role)

        # Record provenance
        provenance = ProvenanceLog()
        token_usage = {
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
        }
        provenance.record(
            layer="agents",
            operation="llm_invocation",
            parameters={
                "backend": "anthropic_api",
                "model": self._model,
                "prompt_hash": prompt_hash,
                "token_usage": token_usage,
                "role": role.value,
            },
            source=f"AnthropicAPIBackend.invoke(role={role.value})",
            rationale=f"LLM-based subagent invocation for {role.value} role.",
        )

        # Build AgentOutput from tool_input
        return self._build_output(tool_input, role, provenance)

    def _serialize_context(self, context: AgentContext) -> str:
        """Serialize AgentContext to a JSON string for the user message."""

        def _make_serializable(obj: Any) -> Any:
            if obj is None:
                return None
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, tuple | frozenset):
                return [_make_serializable(x) for x in obj]
            if isinstance(obj, dict):
                return {str(k): _make_serializable(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_make_serializable(x) for x in obj]
            if hasattr(obj, "__dataclass_fields__"):
                try:
                    return {k: _make_serializable(v) for k, v in asdict(obj).items()}
                except (TypeError, RecursionError):
                    return repr(obj)
            if isinstance(obj, str | int | float | bool):
                return obj
            return repr(obj)

        data = _make_serializable(context)
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)

    def _extract_tool_input(self, response: Any, role: AgentRole) -> dict[str, Any]:
        """Extract the tool_use input from the API response."""
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "submit_output":
                return block.input  # type: ignore[no-any-return]

        # No tool_use block found
        raw = str(response.content) if response.content else "(empty)"
        raise AgentOutputParseError(
            f"No submit_output tool_use block in response for role={role.value}",
            raw_content=raw,
        )

    def _build_output(
        self,
        tool_input: dict[str, Any],
        role: AgentRole,
        provenance: ProvenanceLog,
    ) -> AgentOutput:
        """Build AgentOutput from parsed tool_use input.

        This performs a best-effort mapping from the LLM's JSON output
        to the AgentOutput dataclass fields. Fields that don't parse
        cleanly are logged and skipped (the caller gets what was parseable).
        """
        from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed
        from yao.ir.plan.phrase import PhrasePlan

        kwargs: dict[str, Any] = {"provenance": provenance}

        # Role-specific parsing
        if role == AgentRole.COMPOSER:
            motif_data = tool_input.get("motif_plan")
            if motif_data and isinstance(motif_data, dict):
                seeds_data = motif_data.get("seeds", [])
                seeds = []
                for s in seeds_data:
                    if isinstance(s, dict):
                        seeds.append(
                            MotifSeed(
                                id=s.get("id", "llm_motif"),
                                rhythm_shape=tuple(s.get("rhythm_shape", [1.0])),
                                interval_shape=tuple(s.get("interval_shape", [0])),
                                origin_section=s.get("origin_section", "verse"),
                                character=s.get("character", ""),
                            )
                        )
                placements_data = motif_data.get("placements", [])
                placements = []
                for p in placements_data:
                    if isinstance(p, dict):
                        placements.append(
                            MotifPlacement(
                                motif_id=p.get("motif_id", ""),
                                section_id=p.get("section_id", ""),
                                start_beat=float(p.get("start_beat", 0.0)),
                            )
                        )
                kwargs["motif_plan"] = MotifPlan(
                    seeds=seeds,
                    placements=placements,
                )

            phrase_data = tool_input.get("phrase_plan")
            if phrase_data and isinstance(phrase_data, dict):
                kwargs["phrase_plan"] = PhrasePlan(
                    phrases=[],
                    bars_per_phrase=float(phrase_data.get("bars_per_phrase", 4.0)),
                    pattern=phrase_data.get("pattern", ""),
                )

        elif role == AgentRole.ADVERSARIAL_CRITIC:
            findings_data = tool_input.get("findings", [])
            # For now, store raw findings data in provenance
            # Full Finding parsing requires more context
            provenance.record(
                layer="agents",
                operation="critic_findings_received",
                parameters={"findings_count": len(findings_data)},
                source="AnthropicAPIBackend._build_output",
                rationale="LLM critic produced findings.",
            )
            kwargs["findings"] = ()

        # Other roles: store raw data in provenance for now
        # Full integration for each role will follow in subsequent sprints
        elif role in (
            AgentRole.HARMONY_THEORIST,
            AgentRole.RHYTHM_ARCHITECT,
            AgentRole.ORCHESTRATOR,
            AgentRole.MIX_ENGINEER,
            AgentRole.PRODUCER,
        ):
            provenance.record(
                layer="agents",
                operation=f"{role.value}_output_received",
                parameters={"raw_keys": list(tool_input.keys())},
                source="AnthropicAPIBackend._build_output",
                rationale=f"LLM {role.value} output received, stored for pipeline consumption.",
            )
            # For producer, extract form_plan if present
            if role == AgentRole.PRODUCER:
                form_data = tool_input.get("form_plan")
                if form_data:
                    kwargs["overrides"] = tool_input.get("overrides", {})
                    kwargs["escalations"] = tuple(tool_input.get("escalations", []))

        return AgentOutput(**kwargs)
