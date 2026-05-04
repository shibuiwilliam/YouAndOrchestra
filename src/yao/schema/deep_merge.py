"""Deep merge utility for spec composability.

Recursively merges overlay dicts into base dicts.
Overlay values take precedence. None values in overlay are skipped.
Lists are replaced, not appended (use key+ suffix for append behavior).
"""

from __future__ import annotations

import copy
from typing import Any


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay dict into base dict.

    Args:
        base: The base dictionary (not modified).
        overlay: Values to merge on top (takes precedence).

    Returns:
        New merged dictionary.

    Example:
        >>> deep_merge({"a": 1, "b": {"c": 2}}, {"b": {"d": 3}})
        {'a': 1, 'b': {'c': 2, 'd': 3}}
    """
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
