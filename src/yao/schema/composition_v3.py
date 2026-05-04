"""Composition spec v3 — adds extends/overrides composability.

v3 specs can inherit from base specs or fragments via ``extends``,
then override specific fields with ``overrides``. This enables
compositional spec authoring: combine a genre base, groove fragment,
and instrumentation fragment, then override tempo.

Resolution: ``extends`` are loaded and deep-merged in order (later overrides
earlier), then ``overrides`` are applied on top of the merged result.
The final spec is validated as a standard CompositionSpec.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from yao.errors import SpecValidationError
from yao.schema.composition import CompositionSpec
from yao.schema.deep_merge import deep_merge


def resolve_v3_spec(
    spec_data: dict[str, Any],
    fragments_dir: Path | None = None,
) -> dict[str, Any]:
    """Resolve a v3 spec by processing extends and overrides.

    Args:
        spec_data: Raw YAML dict that may contain ``extends`` and ``overrides``.
        fragments_dir: Directory to search for fragment files.
            Defaults to ``specs/fragments/`` relative to project root.

    Returns:
        Resolved spec dict ready for CompositionSpec validation.

    Raises:
        SpecValidationError: If extends references cannot be found or
            circular extends are detected.
    """
    if fragments_dir is None:
        fragments_dir = Path("specs/fragments")

    extends = spec_data.pop("extends", [])
    overrides = spec_data.pop("overrides", {})

    if not isinstance(extends, list):
        extends = [extends]

    # Start with empty base, merge each extends in order
    merged: dict[str, Any] = {}
    seen: set[str] = set()

    for ref in extends:
        if ref in seen:
            raise SpecValidationError(
                f"Circular extends detected: '{ref}'",
                field="extends",
            )
        seen.add(ref)

        fragment_data = _load_fragment(ref, fragments_dir)
        merged = deep_merge(merged, fragment_data)

    # Merge the spec itself on top of the extended base
    merged = deep_merge(merged, spec_data)

    # Apply overrides last (these are dot-path or direct keys)
    merged = deep_merge(merged, overrides)

    return merged


def load_v3_spec(
    spec_path: Path,
    fragments_dir: Path | None = None,
) -> CompositionSpec:
    """Load and resolve a v3 composition spec from a YAML file.

    Args:
        spec_path: Path to the composition YAML.
        fragments_dir: Directory to search for fragment files.

    Returns:
        Resolved CompositionSpec.

    Raises:
        SpecValidationError: If the spec is invalid.
    """
    try:
        data = yaml.safe_load(spec_path.read_text())
    except Exception as e:
        raise SpecValidationError(
            f"Failed to load spec: {e}",
            field="file",
        ) from e

    if not isinstance(data, dict):
        raise SpecValidationError(
            "Spec must be a YAML mapping",
            field="file",
        )

    resolved = resolve_v3_spec(data, fragments_dir)
    return CompositionSpec.model_validate(resolved)


def is_v3_spec(data: dict[str, Any]) -> bool:
    """Check if a spec dict uses v3 features (extends or overrides).

    Args:
        data: Raw YAML dict.

    Returns:
        True if the spec uses extends or overrides.
    """
    return "extends" in data or "overrides" in data


def _load_fragment(ref: str, fragments_dir: Path) -> dict[str, Any]:
    """Load a fragment YAML by reference.

    Args:
        ref: Fragment reference — either a relative path or a name
            (resolved as ``fragments_dir/<name>.yaml``).
        fragments_dir: Directory to search.

    Returns:
        Fragment data as dict.

    Raises:
        SpecValidationError: If the fragment file is not found.
    """
    # Try as direct path first
    path = Path(ref)
    if path.exists():
        data = yaml.safe_load(path.read_text())
        return data if isinstance(data, dict) else {}

    # Try in fragments directory
    frag_path = fragments_dir / ref
    if frag_path.exists():
        data = yaml.safe_load(frag_path.read_text())
        return data if isinstance(data, dict) else {}

    # Try with .yaml extension
    frag_path = fragments_dir / f"{ref}.yaml"
    if frag_path.exists():
        data = yaml.safe_load(frag_path.read_text())
        return data if isinstance(data, dict) else {}

    raise SpecValidationError(
        f"Fragment not found: '{ref}' (searched {fragments_dir})",
        field="extends",
    )
