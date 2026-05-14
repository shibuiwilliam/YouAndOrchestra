# ADR-0001: Phase 2 — Claude Agent SDK Surface

**Status:** Completed
**Date:** 2026-05-14

## Context

YaO Phase 1 delivered a mature music production engine accessible via CLI
and Claude Code. However, programmatic access (web apps, bots, CI, notebooks)
was impossible without launching an interactive Claude Code session.

## Decision

Implement the Claude Agent SDK as a third peer surface in `src/yao/sdk/`,
following the architecture: Surface → Conductor → Layers 0-7.

## What Was Built

### Phase 2A — Foundation
- In-process MCP server with 15 tools wrapping the Conductor
- `default_yao_options()` builder for `ClaudeAgentOptions`
- Pydantic input models for all tools
- Architecture lint updated (SDK = Layer 8 surface)
- `claude-agent-sdk` added as `[sdk]` extra

### Phase 2B — Lane A Facade
- `YaoAgent` class with 10 async generator methods (1:1 with slash commands)
- 9 typed streaming events (`PhaseStartedEvent`, `IterationCompletedEvent`, etc.)
- Typed result objects (`ComposeResult`, `ConductResult`, etc.)
- JSON Schema models for structured outputs
- Message-to-YaoEvent translator

### Phase 2C — Hooks and Permissions
- 4 standard hooks as Python callbacks (provenance, render, critique, validate)
- `default_yao_permission()` protecting iterations, references, agent definitions
- Enforcement tests proving hooks fire regardless of agent behavior

### Phase 2D — Programmatic Subagents
- Markdown front-matter parser (`_frontmatter.py`)
- `yao_agent_definitions()` returning `dict[str, AgentDefinition]`
- Adversarial Critic with `disallowedTools=["Write", "Edit"]`
- All agents auto-registered with the `yao` MCP server

### Phase 2E — Sessions
- Project-scoped session helpers (list, tag, key generation)

### Phase 2F — Reference Applications
- `examples/sdk/minimal.py` — 5-line compose example
- `examples/sdk/web/` — FastAPI + SSE streaming
- `examples/sdk/discord/` — Discord bot
- `examples/sdk/ci/` — CI music generation
- `examples/sdk/notebook/` — Jupyter demo

### Phase 2G — Documentation
- 6 SDK doc pages (overview, quickstart, API reference, lanes, deployment, parity)

## Consequences

- Any Python program can now compose music via `YaoAgent`
- The same 7-layer engine powers all three surfaces
- No music logic was added to `src/yao/sdk/` — it only wraps
- Architecture lint enforces that layers 0-7 cannot import from `yao.sdk`
- 122+ SDK-specific tests added with no Phase 1 regressions
