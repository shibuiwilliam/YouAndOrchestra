"""Subagent Python implementations — structured judgment for the pipeline.

Each Subagent mirrors a .claude/agents/*.md prompt definition.
Both share the same AgentContext/AgentOutput contract.

- Python Subagents: deterministic logic, ScoreIR manipulation, critique rules
- Claude Code prompts: creative dialogue, sketch-to-spec, natural language
"""

from __future__ import annotations
