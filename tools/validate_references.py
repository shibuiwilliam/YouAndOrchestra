#!/usr/bin/env python3
"""Validate the references catalog for license compliance.

Checks:
1. All entries have a recognized license type.
2. All entries have at least one genre tag.
3. MIDI paths exist for synthetic references.
4. No duplicate IDs.

Usage:
    python tools/validate_references.py
    make validate-refs

Exit codes:
    0: All references valid.
    1: Validation errors found.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "references" / "catalog.yaml"

VALID_LICENSES = {"public_domain", "yao_generated", "cc_by", "cc_by_sa", "cc0", "owned"}


def validate() -> list[str]:
    """Validate the reference catalog.

    Returns:
        List of error messages. Empty if all valid.
    """
    errors: list[str] = []

    if not CATALOG_PATH.exists():
        errors.append(f"Catalog file not found: {CATALOG_PATH}")
        return errors

    with open(CATALOG_PATH) as f:
        data = yaml.safe_load(f) or {}

    refs = data.get("references", [])
    if not refs:
        errors.append("No references found in catalog")
        return errors

    seen_ids: set[str] = set()

    for i, ref in enumerate(refs):
        ref_id = ref.get("id", f"<entry {i}>")

        # Duplicate ID check
        if ref_id in seen_ids:
            errors.append(f"Duplicate reference ID: {ref_id}")
        seen_ids.add(ref_id)

        # Required fields
        for field in ("id", "title", "license", "genre_tags"):
            if field not in ref:
                errors.append(f"{ref_id}: missing required field '{field}'")

        # License type
        license_type = ref.get("license", "")
        if license_type not in VALID_LICENSES:
            errors.append(f"{ref_id}: invalid license '{license_type}'. Valid: {sorted(VALID_LICENSES)}")

        # Genre tags
        tags = ref.get("genre_tags", [])
        if not tags:
            errors.append(f"{ref_id}: must have at least one genre tag")

        # MIDI path existence (only for synthetic — PD files may need download)
        midi_path = ref.get("path_midi", "")
        if midi_path and license_type == "yao_generated":
            full_path = REPO_ROOT / "references" / midi_path
            if not full_path.exists():
                errors.append(f"{ref_id}: MIDI file not found: {full_path}")

    return errors


def main() -> None:
    """Run validation and print results."""
    errors = validate()
    if errors:
        print(f"❌ {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        ref_count = 0
        with open(CATALOG_PATH) as f:
            data = yaml.safe_load(f) or {}
        ref_count = len(data.get("references", []))
        print(f"✅ All {ref_count} references valid.")


if __name__ == "__main__":
    main()
