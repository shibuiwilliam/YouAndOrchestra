"""Genre profile inheritance — additive override resolver.

A child genre (e.g., ``bebop``) declares a ``parent`` (e.g., ``jazz``)
and provides only the fields it wants to override. This module resolves
the full profile by merging parent defaults with child overrides.

Rules:
    - Child values override parent values.
    - ``_add`` suffix fields append to parent lists instead of replacing.
    - Empty lists/dicts in the child do NOT override parent lists/dicts.
    - None values in the child are ignored.

Belongs to Layer 0/1 boundary.
"""

from __future__ import annotations

import copy
from typing import Any

from yao.genre.profile import GenreProfile


def resolve_inheritance(
    child: GenreProfile,
    parent: GenreProfile,
) -> GenreProfile:
    """Merge a child profile with its parent, producing a fully resolved profile.

    The child's explicitly-set fields override the parent's. Fields that are
    at their default value in the child are inherited from the parent.

    Additive fields (suffixed with ``_add``) append to the parent's list
    rather than replacing it. For example, ``chord_palette_extended_add``
    in the child YAML extends the parent's ``chord_palette_extended``.

    Args:
        child: The child genre profile (overrides).
        parent: The parent genre profile (defaults).

    Returns:
        A new GenreProfile with all fields resolved.
    """
    # Get defaults to detect which child fields were explicitly set
    defaults_dict = GenreProfile(name="_default_").model_dump()
    parent_dict = parent.model_dump()
    child_dict = child.model_dump()

    merged = _deep_merge_with_defaults(parent_dict, child_dict, defaults_dict)

    # Handle additive overrides (_add suffix)
    merged = _apply_additive_overrides(merged, child_dict)

    # Preserve child identity
    merged["name"] = child.name
    merged["parent"] = child.parent

    return GenreProfile.model_validate(merged)


def _deep_merge_with_defaults(
    base: dict[str, Any],
    overlay: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    """Recursively merge overlay into base, skipping overlay values at default.

    Only applies overlay values that differ from the model defaults,
    so that a child's unset fields inherit from the parent rather than
    resetting to model defaults.

    Args:
        base: Base dict (parent).
        overlay: Override dict (child).
        defaults: Default values from a fresh GenreProfile instance.

    Returns:
        Merged dict.
    """
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if value is None:
            continue
        if key.endswith("_add"):
            continue  # Handled separately
        if key in ("name", "parent", "description"):
            # Identity fields always come from child
            if _is_non_default(value):
                result[key] = copy.deepcopy(value)
            continue
        default_val = defaults.get(key)
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            default_sub = default_val if isinstance(default_val, dict) else {}
            result[key] = _deep_merge_with_defaults(result[key], value, default_sub)
        elif value != default_val and _is_non_default(value):
            # Only override if child's value differs from model default
            result[key] = copy.deepcopy(value)
    return result


def _apply_additive_overrides(
    merged: dict[str, Any],
    child_dict: dict[str, Any],
) -> dict[str, Any]:
    """Apply ``_add`` suffix fields by appending to the corresponding base field.

    For example, if child has ``chord_palette_extended_add: ["alt", "b13"]``,
    this appends those values to ``merged["chord_palette_extended"]``.

    Args:
        merged: Already-merged dict.
        child_dict: Raw child dict to scan for ``_add`` keys.

    Returns:
        Updated merged dict.
    """
    for key, value in child_dict.items():
        if not key.endswith("_add") or not isinstance(value, list):
            continue
        base_key = key[: -len("_add")]
        if base_key in merged and isinstance(merged[base_key], list):
            # Deduplicate while preserving order
            existing = set(merged[base_key])
            for item in value:
                if item not in existing:
                    merged[base_key].append(item)
                    existing.add(item)
    return merged


def _is_non_default(value: object) -> bool:
    """Check if a value represents an explicit override (not empty/default)."""
    if isinstance(value, list | tuple) and len(value) == 0:
        return False
    if isinstance(value, dict) and len(value) == 0:
        return False
    return value != ""
