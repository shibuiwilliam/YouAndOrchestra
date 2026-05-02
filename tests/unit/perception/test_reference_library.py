"""Tests for reference library — Wave 3.3.

Verifies catalog loading, MIDI availability, and StyleVector extraction.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATALOG_PATH = REPO_ROOT / "references" / "catalog.yaml"
FEATURES_DIR = REPO_ROOT / "references" / "extracted_features"


class TestReferenceCatalog:
    """Tests for references/catalog.yaml."""

    def test_catalog_exists(self) -> None:
        assert CATALOG_PATH.exists()

    def test_catalog_has_references(self) -> None:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        refs = data.get("references", [])
        assert len(refs) >= 5  # At least 5 synthetic

    def test_all_references_have_required_fields(self) -> None:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for ref in data["references"]:
            assert "id" in ref, "Missing id in reference"
            assert "title" in ref, f"Missing title in {ref.get('id')}"
            assert "license" in ref, f"Missing license in {ref.get('id')}"
            assert "source" in ref, f"Missing source in {ref.get('id')}"
            assert "path_midi" in ref, f"Missing path_midi in {ref.get('id')}"

    def test_no_unknown_licenses(self) -> None:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        valid = {"yao_generated", "public_domain", "CC0", "CC-BY"}
        for ref in data["references"]:
            assert ref["license"] in valid, f"{ref['id']}: license '{ref['license']}' is not in {valid}"

    def test_synthetic_midi_files_exist(self) -> None:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for ref in data["references"]:
            if ref["license"] == "yao_generated":
                midi_path = REPO_ROOT / "references" / ref["path_midi"]
                assert midi_path.exists(), f"{ref['id']}: MIDI not found at {midi_path}"

    def test_genre_tags_present(self) -> None:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for ref in data["references"]:
            assert "genre_tags" in ref, f"{ref['id']}: missing genre_tags"
            assert len(ref["genre_tags"]) >= 1, f"{ref['id']}: empty genre_tags"


class TestExtractedFeatures:
    """Tests for pre-computed StyleVectors."""

    def test_features_dir_exists(self) -> None:
        assert FEATURES_DIR.exists()

    def test_all_synthetic_have_features(self) -> None:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for ref in data["references"]:
            if ref["license"] == "yao_generated":
                stem = Path(ref["path_midi"]).stem
                feature_path = FEATURES_DIR / f"{stem}.json"
                assert feature_path.exists(), f"{ref['id']}: no feature file at {feature_path}"

    def test_feature_files_have_required_fields(self) -> None:
        required = {
            "source_midi",
            "sha256_prefix",
            "harmonic_rhythm",
            "voice_leading_smoothness",
            "rhythmic_density_per_bar",
            "register_distribution",
        }
        for json_path in FEATURES_DIR.glob("*.json"):
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            for field in required:
                assert field in data, f"{json_path.name}: missing field '{field}'"

    def test_style_vectors_differ_across_genres(self) -> None:
        """Different genre references should have different StyleVectors."""
        features = {}
        for json_path in sorted(FEATURES_DIR.glob("*.json")):
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            features[json_path.stem] = data["harmonic_rhythm"]

        # At least some should differ
        values = list(features.values())
        assert len(set(values)) > 1, "All StyleVectors have identical harmonic_rhythm"
