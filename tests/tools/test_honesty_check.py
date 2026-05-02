"""Tests for tools/honesty_check.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# Add tools/ to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))

import honesty_check  # noqa: E402


class TestParseFeatureStatuses:
    """Tests for _parse_feature_statuses."""

    def test_parses_stable_feature(self, tmp_path: Path) -> None:
        md = tmp_path / "STATUS.md"
        md.write_text("| Feature | Status |\n|---|---|\n| My Feature | ✅ |\n")
        result = honesty_check._parse_feature_statuses(md)
        assert result["My Feature"] == "✅"

    def test_parses_partial_feature(self, tmp_path: Path) -> None:
        md = tmp_path / "STATUS.md"
        md.write_text("| Feature | Status |\n|---|---|\n| Stub Thing | 🟡 |\n")
        result = honesty_check._parse_feature_statuses(md)
        assert result["Stub Thing"] == "🟡"

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        result = honesty_check._parse_feature_statuses(tmp_path / "missing.md")
        assert result == {}

    def test_skips_header_rows(self, tmp_path: Path) -> None:
        md = tmp_path / "STATUS.md"
        md.write_text("| Feature | Status |\n|---|---|\n| Real | ✅ |\n")
        result = honesty_check._parse_feature_statuses(md)
        assert "Feature" not in result
        assert "---" not in result


class TestIsFeatureStable:
    """Tests for _is_feature_stable."""

    def test_stable_feature(self) -> None:
        statuses = {"My Feature": "✅"}
        assert honesty_check._is_feature_stable("My Feature", statuses) is True

    def test_partial_feature(self) -> None:
        statuses = {"My Feature": "🟡"}
        assert honesty_check._is_feature_stable("My Feature", statuses) is False


class TestCheckComposerSubagent:
    """Tests for check_composer_subagent."""

    def test_detects_empty_motif_plan(self, tmp_path: Path) -> None:
        result = honesty_check.HonestyCheckResult()
        composer = tmp_path / "src" / "yao" / "subagents" / "composer.py"
        composer.parent.mkdir(parents=True)
        composer.write_text("motif_plan = MotifPlan(seeds=[], placements=[])\n")
        with patch.object(honesty_check, "REPO_ROOT", tmp_path):
            honesty_check.check_composer_subagent(result)
        assert len(result.findings) == 1
        assert "empty MotifPlan" in result.findings[0].indicator

    def test_passes_non_empty_plan(self, tmp_path: Path) -> None:
        result = honesty_check.HonestyCheckResult()
        composer = tmp_path / "src" / "yao" / "subagents" / "composer.py"
        composer.parent.mkdir(parents=True)
        composer.write_text("motif_plan = MotifPlan(seeds=[seed1], placements=[p1])\n")
        with patch.object(honesty_check, "REPO_ROOT", tmp_path):
            honesty_check.check_composer_subagent(result)
        assert result.passed == 1


class TestCheckAnthropicBackend:
    """Tests for check_anthropic_backend."""

    def test_detects_fallback_delegation(self, tmp_path: Path) -> None:
        result = honesty_check.HonestyCheckResult()
        backend = tmp_path / "src" / "yao" / "agents" / "anthropic_api_backend.py"
        backend.parent.mkdir(parents=True)
        backend.write_text("return self._fallback.invoke(role, context)\n")
        with patch.object(honesty_check, "REPO_ROOT", tmp_path):
            honesty_check.check_anthropic_backend(result)
        assert len(result.findings) == 1
        assert "fallback" in result.findings[0].indicator.lower()

    def test_warns_missing_is_stub(self, tmp_path: Path) -> None:
        result = honesty_check.HonestyCheckResult()
        backend = tmp_path / "src" / "yao" / "agents" / "anthropic_api_backend.py"
        backend.parent.mkdir(parents=True)
        backend.write_text("class AnthropicAPIBackend:\n    pass\n")
        with patch.object(honesty_check, "REPO_ROOT", tmp_path):
            honesty_check.check_anthropic_backend(result)
        assert any("is_stub" in f.indicator for f in result.findings)


class TestCheckGenreSkillsIntegration:
    """Tests for check_genre_skills_integration."""

    def test_detects_unintegrated_skills(self, tmp_path: Path) -> None:
        result = honesty_check.HonestyCheckResult()
        skills_dir = tmp_path / ".claude" / "skills" / "genres"
        skills_dir.mkdir(parents=True)
        (skills_dir / "jazz.md").write_text("---\ngenre: jazz\n---\n# Jazz\n")
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')\n")
        with patch.object(honesty_check, "REPO_ROOT", tmp_path):
            honesty_check.check_genre_skills_integration(result)
        assert len(result.findings) == 1
        assert "0 references from src/" in result.findings[0].indicator


class TestMainExitCode:
    """Tests for main() exit code logic."""

    def test_returns_zero_when_stubs_are_acknowledged(self) -> None:
        # When features are 🟡, errors become info → exit 0
        with (
            patch.object(honesty_check, "_parse_feature_statuses", return_value={}),
            patch.object(honesty_check, "ALL_CHECKS", []),
        ):
            assert honesty_check.main() == 0
