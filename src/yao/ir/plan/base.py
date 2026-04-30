"""Base types for MPIR plan components.

All plan components are frozen dataclasses and support dict serialization
for JSON persistence and provenance tracking.
"""

from __future__ import annotations

import json
from typing import Any, Protocol


class PlanComponent(Protocol):
    """Protocol for all MPIR components.

    Every plan component must be serializable to/from dict for
    JSON persistence and provenance recording.
    """

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanComponent:
        """Deserialize from a plain dict."""
        ...


def plan_to_json(component: Any) -> str:
    """Serialize a plan component to JSON string.

    Args:
        component: A plan component with a to_dict() method.

    Returns:
        JSON string.
    """
    return json.dumps(component.to_dict(), ensure_ascii=False, indent=2)


def plan_from_json(json_str: str) -> dict[str, Any]:
    """Deserialize a JSON string to a raw dict.

    The caller is responsible for passing this to the appropriate
    from_dict() class method.

    Args:
        json_str: JSON string.

    Returns:
        Parsed dict.
    """
    result: dict[str, Any] = json.loads(json_str)
    return result
