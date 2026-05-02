"""Tests for tools/check_skill_grounding.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))

import check_skill_grounding  # noqa: E402


class TestParseFrontmatter:
    """Tests for _parse_frontmatter."""

    def test_extracts_genre_id(self, tmp_path: Path) -> None:
        md = tmp_path / "jazz.md"
        md.write_text("---\ngenre: jazz_swing\ntempo_range: [100, 200]\n---\n# Jazz\n")
        result = check_skill_grounding._parse_frontmatter(md)
        assert result["genre"] == "jazz_swing"

    def test_handles_no_frontmatter(self, tmp_path: Path) -> None:
        md = tmp_path / "plain.md"
        md.write_text("# No frontmatter here\n")
        result = check_skill_grounding._parse_frontmatter(md)
        assert result == {}

    def test_handles_empty_frontmatter(self, tmp_path: Path) -> None:
        md = tmp_path / "empty.md"
        md.write_text("---\n---\n# Empty frontmatter\n")
        result = check_skill_grounding._parse_frontmatter(md)
        assert result == {}


class TestFindSkillReferences:
    """Tests for _find_skill_references."""

    def test_finds_reference_in_src(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        py_file = src_dir / "loader.py"
        py_file.write_text('genre = "cinematic"\nload_genre("cinematic")\n')
        with (
            patch.object(check_skill_grounding, "SRC_DIR", src_dir),
            patch.object(check_skill_grounding, "REPO_ROOT", tmp_path),
        ):
            refs = check_skill_grounding._find_skill_references("cinematic")
        assert len(refs) > 0

    def test_no_reference_found(self, tmp_path: Path) -> None:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        py_file = src_dir / "main.py"
        py_file.write_text('print("hello")\n')
        with (
            patch.object(check_skill_grounding, "SRC_DIR", src_dir),
            patch.object(check_skill_grounding, "REPO_ROOT", tmp_path),
        ):
            refs = check_skill_grounding._find_skill_references("nonexistent_genre")
        assert refs == []


class TestMainExitCode:
    """Tests for main()."""

    def test_returns_zero_non_strict_with_ungrounded(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / ".claude" / "skills" / "genres"
        skills_dir.mkdir(parents=True)
        (skills_dir / "jazz.md").write_text("---\ngenre: jazz\n---\n# Jazz\n")
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('no genre refs')\n")
        with (
            patch.object(check_skill_grounding, "REPO_ROOT", tmp_path),
            patch.object(check_skill_grounding, "SKILLS_DIR", skills_dir),
            patch.object(check_skill_grounding, "SRC_DIR", src_dir),
            patch.object(sys, "argv", ["check_skill_grounding.py"]),
        ):
            result = check_skill_grounding.main()
        assert result == 0  # non-strict

    def test_returns_one_strict_with_ungrounded(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / ".claude" / "skills" / "genres"
        skills_dir.mkdir(parents=True)
        (skills_dir / "jazz.md").write_text("---\ngenre: jazz\n---\n# Jazz\n")
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('no genre refs')\n")
        with (
            patch.object(check_skill_grounding, "REPO_ROOT", tmp_path),
            patch.object(check_skill_grounding, "SKILLS_DIR", skills_dir),
            patch.object(check_skill_grounding, "SRC_DIR", src_dir),
            patch.object(sys, "argv", ["check_skill_grounding.py", "--strict"]),
        ):
            result = check_skill_grounding.main()
        assert result == 1
