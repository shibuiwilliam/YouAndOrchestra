"""LLM quality comparison: PythonOnly vs Anthropic API for motif generation.

Requires ANTHROPIC_API_KEY. Skipped in CI.
"""

from __future__ import annotations

import pytest

from tests.llm_quality.conftest import requires_anthropic_key


@requires_anthropic_key
class TestMotifQualityComparison:
    """Compare motif generation quality between backends."""

    def test_llm_produces_non_empty_motif_plan(self):
        """LLM backend must produce at least one motif seed."""
        from yao.agents.anthropic_api_backend import AnthropicAPIBackend

        # This test requires real API access — skipped without key
        AnthropicAPIBackend()

        # Minimal real context would go here
        # For now, this serves as a placeholder for quality comparison
        pytest.skip("Full context setup needed for real API test")
