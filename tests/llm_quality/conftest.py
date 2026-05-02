"""Configuration for LLM quality tests.

These tests require a real Anthropic API key AND the anthropic package.
Skipped in CI and when dependencies are missing.
Run with: pytest tests/llm_quality/ -m requires_anthropic_key
"""

from __future__ import annotations

import os

import pytest


def _anthropic_available() -> bool:
    """Check if both API key and anthropic package are available."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401

        return True
    except ImportError:
        return False


requires_anthropic_key = pytest.mark.skipif(
    not _anthropic_available(),
    reason="ANTHROPIC_API_KEY not set or anthropic package not installed",
)
