# Design: Wave 1.2 — Anthropic API Backend

> **Date**: 2026-05-03
> **Status**: Implementation
> **Sprint**: Wave 1.2

---

## 1. Overview

Replace the stub `AnthropicAPIBackend` with a real implementation that:
- Calls the Anthropic Messages API via the official SDK
- Uses `.claude/agents/<role>.md` files as system prompts
- Enforces structured output via tool use
- Records full provenance (backend, model, prompt_hash, token_usage)
- Never silently falls back to PythonOnlyBackend

## 2. System Prompt Strategy

Each `.claude/agents/<role>.md` file is read at `__init__` time and cached.
The role is mapped via `AgentRole.value` → filename:
- `AgentRole.COMPOSER` → `.claude/agents/composer.md`
- `AgentRole.ADVERSARIAL_CRITIC` → `.claude/agents/adversarial-critic.md`

The entire markdown content becomes the system prompt. No transformation needed.

## 3. Context Serialization

`AgentContext` (frozen dataclass) is serialized to a JSON user message:
```json
{
  "spec": { ... },
  "intent": { ... },
  "trajectory": { ... },
  "form_plan": null | { ... },
  "harmony_plan": null | { ... },
  ...
}
```

Serialization uses `dataclasses.asdict()` with custom handlers for:
- `Enum` → `.value`
- `tuple` → `list`
- `frozenset` → `list`
- Non-serializable objects → `repr()`

## 4. Output Schema (Tool Use)

The LLM is forced to call a tool named `submit_output` whose schema matches
the fields that the given role is expected to produce:

| Role | Expected output fields |
|---|---|
| COMPOSER | motif_plan, phrase_plan |
| HARMONY_THEORIST | harmony_plan |
| RHYTHM_ARCHITECT | drum_pattern |
| ORCHESTRATOR | arrangement_plan |
| ADVERSARIAL_CRITIC | findings |
| MIX_ENGINEER | production_manifest |
| PRODUCER | form_plan, overrides, escalations |

The tool input schema is a simplified JSON Schema per role.
Parsing uses the tool_use content block from the response.

## 5. Error Handling

| Situation | Response |
|---|---|
| No API key | `BackendNotConfiguredError` at `__init__` |
| API rate limit | Let SDK retry (default behavior) |
| Malformed tool_use response | `AgentOutputParseError` |
| API error (500, etc.) | `AgentBackendError` |
| Timeout | `AgentBackendError` with timeout info |

**No silent fallback.** If the API call fails, raise an exception.

## 6. Provenance Recording

Every invocation records an `LLMCallRecord` in provenance:
- `backend_name`: "anthropic_api"
- `model`: model string (e.g., "claude-sonnet-4-6")
- `prompt_hash`: SHA-256 of (system + user message)
- `token_usage`: `{"input": N, "output": M}`
- `cost_estimate_usd`: computed from token counts

## 7. Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | API authentication | None (required) |
| `YAO_AGENT_BACKEND` | Backend selection | "python_only" |
| `YAO_LLM_MODEL` | Model override | "claude-sonnet-4-6" |

## 8. Cost Safety

A session-level counter tracks total LLM calls. At 100 calls, emit a
`structlog.warning`. This is advisory only — not an error.

## 9. Test Strategy

- **Unit tests** (mock): `tests/unit/agents/test_anthropic_api_backend.py`
  - All API calls mocked via `unittest.mock.patch`
  - Tests focus on serialization, parsing, error handling, provenance
- **Quality tests** (optional): `tests/llm_quality/`
  - Require real API key, skipped in CI
  - Compare PythonOnly vs LLM output quality
