#!/usr/bin/env python3
"""Extract StyleVector features from reference MIDI files.

Reads each reference from catalog.yaml, extracts a StyleVector,
and writes the result to references/extracted_features/<id>.json.

Usage:
    python tools/extract_features.py
    python tools/extract_features.py --id synth-baroque-001

Only processes references whose MIDI files exist locally.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "references" / "catalog.yaml"
FEATURES_DIR = REPO_ROOT / "references" / "extracted_features"


def extract_for_reference(ref: dict, repo_root: Path) -> dict | None:
    """Extract features for a single reference.

    Args:
        ref: Reference entry from catalog.yaml.
        repo_root: Repository root path.

    Returns:
        Dict of extracted features, or None if MIDI not available.
    """
    midi_path = repo_root / "references" / ref.get("path_midi", "")
    if not midi_path.exists():
        return None

    # Import here to avoid import-time cost
    from yao.render.midi_reader import read_midi

    score = read_midi(midi_path)

    from yao.perception.style_vector import extract_style_vector_from_score

    sv = extract_style_vector_from_score(score)

    return {
        "id": ref["id"],
        "genre_tags": ref.get("genre_tags", []),
        "harmonic_rhythm": sv.harmonic_rhythm,
        "voice_leading_smoothness": sv.voice_leading_smoothness,
        "motif_density": sv.motif_density,
        "rhythm_complexity": sv.rhythm_complexity,
        "rhythmic_density_per_bar": list(sv.rhythmic_density_per_bar),
        "register_distribution": list(sv.register_distribution),
        "interval_class_histogram": list(sv.interval_class_histogram),
        "chord_quality_histogram": list(sv.chord_quality_histogram),
        "cadence_type_distribution": list(sv.cadence_type_distribution),
    }


def main() -> None:
    """Run feature extraction."""
    parser = argparse.ArgumentParser(description="Extract StyleVector features from references.")
    parser.add_argument("--id", help="Extract for a specific reference ID only.")
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print(f"❌ Catalog not found: {CATALOG_PATH}")
        sys.exit(1)

    with open(CATALOG_PATH) as f:
        data = yaml.safe_load(f) or {}

    refs = data.get("references", [])
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    extracted = 0
    skipped = 0

    for ref in refs:
        ref_id = ref.get("id", "")
        if args.id and ref_id != args.id:
            continue

        features = extract_for_reference(ref, REPO_ROOT)
        if features is None:
            skipped += 1
            continue

        out_path = FEATURES_DIR / f"{ref_id}.json"
        with open(out_path, "w") as f:
            json.dump(features, f, indent=2)

        extracted += 1

    print(f"✅ Extracted features for {extracted} references ({skipped} skipped — MIDI not available).")


if __name__ == "__main__":
    main()
