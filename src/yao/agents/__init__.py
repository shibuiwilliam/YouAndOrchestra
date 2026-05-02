"""Backend-Agnostic Agent Protocol — pluggable LLM/Python execution.

Provides a unified ``AgentBackend`` interface that all backends implement.
The Conductor uses this protocol to invoke Subagents without knowing
which backend (Claude Code, Anthropic API, local LLM, or pure Python)
is doing the actual work.

Default backend: ``PythonOnlyBackend`` (no LLM required, CI-safe).
"""

from __future__ import annotations
