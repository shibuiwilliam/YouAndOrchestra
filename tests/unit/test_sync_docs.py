"""Tests for document sync checker."""

from __future__ import annotations

from pathlib import Path

from tools.sync_docs import check_consistency, parse_claude_tier_items, parse_feature_status


class TestFeatureStatusParsing:
    def test_parseable(self) -> None:
        features = parse_feature_status(Path("FEATURE_STATUS.md"))
        assert len(features) > 0

    def test_has_stable_features(self) -> None:
        features = parse_feature_status(Path("FEATURE_STATUS.md"))
        stable = [f for f, s in features.items() if s == "✅"]
        assert len(stable) > 0


class TestClaudeMdParsing:
    def test_parseable(self) -> None:
        # May have 0 items if all are done
        items = parse_claude_tier_items(Path("CLAUDE.md"))
        assert isinstance(items, list)


class TestConsistency:
    def test_no_errors(self) -> None:
        errors, warnings = check_consistency()
        assert len(errors) == 0, f"Sync errors: {errors}"
