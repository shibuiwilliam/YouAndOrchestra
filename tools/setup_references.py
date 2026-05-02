#!/usr/bin/env python3
"""Download public domain MIDI files for the reference library.

Downloads MIDI files from public domain sources (IMSLP, Mutopia Project)
for entries in references/catalog.yaml that have license=public_domain
and whose MIDI files are not yet present locally.

Usage:
    python tools/setup_references.py
    make setup-references
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "references" / "catalog.yaml"
REFERENCES_DIR = REPO_ROOT / "references"

# Known download URLs for public domain MIDI files
# These are from Mutopia Project and similar CC0/PD sources
_DOWNLOAD_URLS: dict[str, str] = {
    # Placeholder URLs — these would point to actual PD MIDI sources
    # Users should download manually from IMSLP or Mutopia Project
    # and place files in the correct paths
}


def main() -> int:
    """Check which PD references are missing and provide instructions."""
    if not CATALOG_PATH.exists():
        print("ERROR: references/catalog.yaml not found")
        return 1

    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    refs = catalog.get("references", [])
    pd_refs = [r for r in refs if r.get("license") == "public_domain"]
    synthetic_refs = [r for r in refs if r.get("license") == "yao_generated"]

    # Check synthetic refs
    synth_missing = []
    for ref in synthetic_refs:
        midi_path = REFERENCES_DIR / ref["path_midi"]
        if not midi_path.exists():
            synth_missing.append(ref)

    if synth_missing:
        print(f"WARNING: {len(synth_missing)} synthetic MIDI files missing.")
        print("Run the generation script to recreate them.")
        for ref in synth_missing:
            print(f"  Missing: {ref['path_midi']}")
        print()

    # Check PD refs
    pd_missing = []
    pd_present = []
    for ref in pd_refs:
        midi_path = REFERENCES_DIR / ref["path_midi"]
        if midi_path.exists():
            pd_present.append(ref)
        else:
            pd_missing.append(ref)

    print("Reference Library Status:")
    print(f"  Synthetic: {len(synthetic_refs) - len(synth_missing)}/{len(synthetic_refs)} present")
    print(f"  Public Domain: {len(pd_present)}/{len(pd_refs)} present")
    print()

    if pd_missing:
        print(f"Missing {len(pd_missing)} public domain MIDI files:")
        print()
        (REFERENCES_DIR / "midi" / "public_domain").mkdir(parents=True, exist_ok=True)
        for ref in pd_missing:
            print(f"  {ref['id']}:")
            print(f"    Title: {ref['title']}")
            print(f"    Source: {ref['source']}")
            print(f"    Place at: references/{ref['path_midi']}")
            print()
        print("Download MIDI files from IMSLP (https://imslp.org) or")
        print("Mutopia Project (https://www.mutopiaproject.org) and place")
        print("them at the paths listed above.")
        print()
        print("Only download works that are PUBLIC DOMAIN in your jurisdiction.")

    if not pd_missing and not synth_missing:
        print("OK: All reference MIDI files are present.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
