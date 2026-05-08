#!/usr/bin/env python3
"""Audit all genre profile YAMLs against the GenreProfile Pydantic schema.

Validates every YAML in src/yao/genre/profiles/ can be loaded and passes
basic completeness checks. Also validates legacy profiles in genre_profiles/.

Run via: python tools/audit_genres.py
Exit code: 0 if all pass, 1 if any fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from yao.genre.profile import GenreProfile
from yao.genre.registry import GenreRegistry


def audit_profiles_directory(directory: Path) -> tuple[int, list[str]]:
    """Validate all YAML profiles in a directory.

    Args:
        directory: Path to the profiles directory.

    Returns:
        Tuple of (count_ok, list_of_errors).
    """
    if not directory.exists():
        return 0, []

    count_ok = 0
    errors: list[str] = []

    for yaml_path in sorted(directory.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{yaml_path.name}: YAML parse error — {e}")
            continue

        if not isinstance(data, dict):
            errors.append(f"{yaml_path.name}: root is not a mapping")
            continue

        if "name" not in data:
            errors.append(f"{yaml_path.name}: missing required 'name' field")
            continue

        try:
            profile = GenreProfile.from_yaml_data(data)
        except Exception as e:
            errors.append(f"{yaml_path.name}: Pydantic validation error — {e}")
            continue

        # Check completeness (only for non-child profiles)
        if profile.parent is None:
            try:
                profile.validate_complete()
            except Exception as e:
                errors.append(f"{yaml_path.name}: incomplete — {e}")
                continue

        count_ok += 1

    return count_ok, errors


def main() -> int:
    """Run the genre audit."""
    project_root = Path(__file__).resolve().parent.parent
    v2_dir = project_root / "src" / "yao" / "genre" / "profiles"
    legacy_dir = project_root / "genre_profiles"

    total_ok = 0
    all_errors: list[str] = []

    # Audit v2.0 profiles
    count, errors = audit_profiles_directory(v2_dir)
    total_ok += count
    all_errors.extend(errors)

    # Audit legacy profiles
    count, errors = audit_profiles_directory(legacy_dir)
    total_ok += count
    all_errors.extend(errors)

    # Also verify registry loads everything
    try:
        GenreRegistry.reload()
        registry_count = len(GenreRegistry.all())
    except Exception as e:
        all_errors.append(f"Registry load failed: {e}")
        registry_count = 0

    if all_errors:
        print(f"audit-genres: {len(all_errors)} error(s) found\n")
        for err in all_errors:
            print(f"  ERROR: {err}")
        return 1

    print(f"audit-genres: {total_ok} profile YAMLs validated, {registry_count} genres in registry — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
