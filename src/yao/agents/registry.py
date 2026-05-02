"""Agent backend registry — selects backend by name or environment variable.

Selection order:
1. Explicit ``get_backend(name)`` call
2. ``YAO_AGENT_BACKEND`` environment variable
3. Default: ``python_only``

Belongs to agents/ package (Tier 4).
"""

from __future__ import annotations

import os

from yao.agents.anthropic_api_backend import AnthropicAPIBackend
from yao.agents.claude_code_backend import ClaudeCodeBackend
from yao.agents.protocol import AgentBackend
from yao.agents.python_only_backend import PythonOnlyBackend

_BACKENDS: dict[str, type[AgentBackend]] = {
    "python_only": PythonOnlyBackend,
    "anthropic_api": AnthropicAPIBackend,
    "claude_code": ClaudeCodeBackend,
}

_ENV_VAR = "YAO_AGENT_BACKEND"
_DEFAULT = "python_only"


def get_backend(name: str | None = None) -> AgentBackend:
    """Get an agent backend by name.

    Args:
        name: Backend name. If None, reads from ``YAO_AGENT_BACKEND``
            env var, defaulting to ``python_only``.

    Returns:
        An AgentBackend instance.

    Raises:
        KeyError: If the backend name is not registered.
    """
    if name is None:
        name = os.environ.get(_ENV_VAR, _DEFAULT)

    cls = _BACKENDS.get(name)
    if cls is None:
        available = sorted(_BACKENDS.keys())
        msg = f"Unknown agent backend '{name}'. Available: {available}"
        raise KeyError(msg)

    return cls()


def available_backends() -> list[str]:
    """Return sorted list of registered backend names."""
    return sorted(_BACKENDS.keys())
