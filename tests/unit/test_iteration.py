"""Tests for the iteration management module."""

from __future__ import annotations

from pathlib import Path

from yao.render.iteration import current_iteration, list_iterations, next_iteration_dir


class TestIteration:
    def test_first_iteration(self, tmp_path: Path) -> None:
        result = next_iteration_dir(tmp_path)
        assert result.name == "v001"
        assert "iterations" in str(result)

    def test_auto_increment(self, tmp_path: Path) -> None:
        iterations_dir = tmp_path / "iterations"
        iterations_dir.mkdir()
        (iterations_dir / "v001").mkdir()
        (iterations_dir / "v002").mkdir()

        result = next_iteration_dir(tmp_path)
        assert result.name == "v003"

    def test_list_iterations_empty(self, tmp_path: Path) -> None:
        result = list_iterations(tmp_path)
        assert result == []

    def test_list_iterations_sorted(self, tmp_path: Path) -> None:
        iterations_dir = tmp_path / "iterations"
        iterations_dir.mkdir()
        (iterations_dir / "v003").mkdir()
        (iterations_dir / "v001").mkdir()
        (iterations_dir / "v002").mkdir()

        result = list_iterations(tmp_path)
        assert [p.name for p in result] == ["v001", "v002", "v003"]

    def test_current_iteration(self, tmp_path: Path) -> None:
        iterations_dir = tmp_path / "iterations"
        iterations_dir.mkdir()
        (iterations_dir / "v001").mkdir()
        (iterations_dir / "v002").mkdir()

        result = current_iteration(tmp_path)
        assert result is not None
        assert result.name == "v002"

    def test_current_iteration_none(self, tmp_path: Path) -> None:
        result = current_iteration(tmp_path)
        assert result is None

    def test_ignores_non_version_dirs(self, tmp_path: Path) -> None:
        iterations_dir = tmp_path / "iterations"
        iterations_dir.mkdir()
        (iterations_dir / "v001").mkdir()
        (iterations_dir / "temp").mkdir()
        (iterations_dir / "backup").mkdir()

        result = list_iterations(tmp_path)
        assert len(result) == 1
        assert result[0].name == "v001"
