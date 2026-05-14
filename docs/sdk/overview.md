# YaO Agent SDK — Overview

The YaO Agent SDK provides programmatic access to the same music production
orchestra available in Claude Code, from any Python program.

## What It Is

The SDK is one of three peer surfaces in YaO:

| Surface | Entry point | Best for |
|---|---|---|
| **Claude Code** | Interactive session | Day-to-day composition |
| **CLI** | `yao` commands | Scripts, CI, one-offs |
| **Agent SDK** | `YaoAgent` | Web apps, bots, notebooks, batch |

All three surfaces call the same Conductor and the same seven-layer engine.
Changing a subagent definition in `.claude/agents/composer.md` affects both
Claude Code and the SDK — one source of truth.

## Two Lanes

- **Lane A — `YaoAgent`**: High-level facade. Five lines to compose music.
- **Lane B — `default_yao_options`**: Full SDK control for power users.

## Quick Example

```python
from yao.sdk import YaoAgent

async with YaoAgent(project="my-song") as agent:
    async for event in agent.conduct("a calm piano piece in D minor"):
        print(event)
```

## Key Concepts

- **In-process MCP server**: 15 tools wrapping the Conductor and engine
- **Streaming events**: Real-time progress (phases, iterations, audio)
- **Typed results**: Pydantic models for every operation
- **Hooks**: Auto-render, auto-critique, auto-provenance
- **Permissions**: Protected paths during music sessions
- **Programmatic subagents**: AgentDefinition mirrors of Markdown agents with per-role tool restrictions and effort tuning
- **Lifecycle control**: `interrupt()` to abort mid-stream, `set_permission_mode()` to adjust at runtime
- **Structured errors**: Domain errors carry schema-friendly payloads for agent-driven recovery
- **CLI integration**: `yao agent` for SDK-driven one-shot composition, `yao serve` for headless HTTP server
