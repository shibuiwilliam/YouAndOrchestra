# Design Note 0005: Subagent Protocol Standardization

> PR-5 | Status: Implemented | Date: 2026-05-05

## Problem

In v1.0, provenance records did not identify which subagent made a decision
or during which cognitive phase. This made it impossible to trace accountability
or understand the decision-making flow across the orchestra.

## Solution

1. Extended `ProvenanceRecord` with optional v2.0 fields:
   - `agent: str | None` — subagent identifier
   - `phase: str | None` — cognitive phase name
   - `confidence: float | None` — decision confidence [0.0, 1.0]
   - `alternatives_rejected: tuple[str, ...]` — options not chosen
   - `skill_referenced: str | None` — genre Skill that informed the decision

2. Created `SubagentMessage` frozen dataclass as the canonical inter-agent
   message format (in `src/yao/conductor/subagent_message.py`).

3. Documented the protocol in `.claude/agents/_protocol.md`.

## Backward Compatibility

All new fields are Optional with defaults (None or empty tuple). Existing code
that creates ProvenanceRecords without these fields continues to work unchanged.

## Files

- `src/yao/reflect/provenance.py` — extended ProvenanceRecord and ProvenanceLog
- `src/yao/conductor/subagent_message.py` — new SubagentMessage, Decision, Question
- `.claude/agents/_protocol.md` — protocol documentation
- `tests/unit/test_subagent_protocol.py` — 12 tests
