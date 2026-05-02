# Wave 1.2 Comparison: AnthropicAPIBackend vs PythonOnlyBackend

> **Date**: 2026-05-03
> **Status**: Implementation complete (mock-verified)
> **Real API test**: Requires ANTHROPIC_API_KEY (not available in this session)

---

## Architecture Comparison

| Aspect | PythonOnlyBackend | AnthropicAPIBackend |
|---|---|---|
| **Execution** | Direct Python SubagentBase.process() | Anthropic Messages API call |
| **is_stub** | N/A (not an LLM wrapper) | `False` |
| **System prompt** | None (code IS the logic) | `.claude/agents/<role>.md` loaded at init |
| **Input format** | Python AgentContext dataclass | JSON-serialized AgentContext |
| **Output parsing** | Direct AgentOutput construction | Tool use `submit_output` → parse → AgentOutput |
| **Error handling** | Python exceptions | AgentBackendError (no silent fallback) |
| **Cost** | Zero | ~500-2000 tokens per call |
| **Latency** | <10ms | 1-5s (API round-trip) |
| **Determinism** | Depends on generator (rule_based=yes) | Non-deterministic (LLM temperature) |

## Provenance Comparison

### PythonOnlyBackend provenance record:
```json
{
  "timestamp": "2026-05-03T...",
  "layer": "subagent",
  "operation": "composer_process",
  "parameters": {"seed": 42, "strategy": "rule_based"},
  "source": "ComposerSubagent.process",
  "rationale": "Generating motif seeds from intent keywords."
}
```

### AnthropicAPIBackend provenance record:
```json
{
  "timestamp": "2026-05-03T...",
  "layer": "agents",
  "operation": "llm_invocation",
  "parameters": {
    "backend": "anthropic_api",
    "model": "claude-sonnet-4-6",
    "prompt_hash": "a1b2c3d4e5f67890",
    "token_usage": {"input": 500, "output": 200},
    "role": "composer"
  },
  "source": "AnthropicAPIBackend.invoke(role=composer)",
  "rationale": "LLM-based subagent invocation for composer role."
}
```

## Key Differences in Output

| Output Field | PythonOnly | Anthropic API |
|---|---|---|
| `motif_plan.seeds` | Generated via Markov bigram model | LLM-creative (potentially richer) |
| `motif_plan.placements` | Rule-based placement strategy | LLM-determined placements |
| `phrase_plan` | Template-based | LLM-creative |
| **Traceability** | Full (algorithm parameters) | Partial (prompt_hash, can replay) |

## Status After Wave 1.2

- `make backend-honesty` → **PASS** (0 violations, was 2)
- `make honesty-check` → **PASS** (0 errors)
- All 1033 unit tests → **PASS**
- AnthropicAPIBackend tests (12) → **PASS** (mocked)
- Backend parity tests (3) → **PASS**

## What's NOT Done (future Waves)

- ClaudeCodeBackend remains `is_stub=True` (Wave 3+)
- Full output parsing for all 7 roles (currently: Composer complete, others store raw in provenance)
- Real API quality comparison (needs `yao[llm-eval]` and ANTHROPIC_API_KEY)
- Cost optimization (caching, smaller models for simple roles)
- Streaming for long-running generations

## Vertical Alignment Assessment

- **Input**: △ (NL→spec still keyword-based, Wave 1.3 will improve)
- **Processing**: ✅ (LLM-backed subagents now possible for richer generation)
- **Evaluation**: △ (Critic can now potentially run via LLM for deeper analysis, but not yet integrated)
