"""Agent backend registry — selects backend by name or environment variable.

Selection order:
1. Explicit ``get_backend(name)`` call
2. ``YAO_AGENT_BACKEND`` environment variable
3. Default: ``python_only``

Belongs to agents/ package (Tier 4).
"""

from __future__ import annotations

import os
from typing import Any

from yao.agents.protocol import AgentBackend

_ENV_VAR = "YAO_AGENT_BACKEND"
_DEFAULT = "python_only"


def _create_python_only() -> AgentBackend:
    """Create PythonOnlyBackend instance."""
    from yao.agents.python_only_backend import PythonOnlyBackend

    return PythonOnlyBackend()


def _create_anthropic_api() -> AgentBackend:
    """Create AnthropicAPIBackend instance (requires API key)."""
    from yao.agents.anthropic_api_backend import AnthropicAPIBackend

    return AnthropicAPIBackend()


def _create_claude_code() -> AgentBackend:
    """Create ClaudeCodeBackend instance."""
    from yao.agents.claude_code_backend import ClaudeCodeBackend

    return ClaudeCodeBackend()


_BACKEND_FACTORIES: dict[str, Any] = {
    "python_only": _create_python_only,
    "anthropic_api": _create_anthropic_api,
    "claude_code": _create_claude_code,
}


def get_backend(name: str | None = None) -> AgentBackend:
    """Get an agent backend by name.

    Args:
        name: Backend name. If None, reads from ``YAO_AGENT_BACKEND``
            env var, defaulting to ``python_only``.

    Returns:
        An AgentBackend instance.

    Raises:
        KeyError: If the backend name is not registered.
        BackendNotConfiguredError: If the backend requires configuration
            that is missing (e.g., API key for anthropic_api).
    """
    if name is None:
        name = os.environ.get(_ENV_VAR, _DEFAULT)

    factory = _BACKEND_FACTORIES.get(name)
    if factory is None:
        available = sorted(_BACKEND_FACTORIES.keys())
        msg = f"Unknown agent backend '{name}'. Available: {available}"
        raise KeyError(msg)

    return factory()  # type: ignore[no-any-return]


def available_backends() -> list[str]:
    """Return sorted list of registered backend names."""
    return sorted(_BACKEND_FACTORIES.keys())
