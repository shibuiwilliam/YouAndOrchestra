"""Tests for yao rate and yao reflect ingest CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from cli.main import cli


class TestRateCommand:
    """Tests for yao rate."""

    def test_rate_creates_json_file(self, tmp_path: Path) -> None:
        """yao rate should create a rating JSON file."""
        # Create a fake iteration directory
        iter_dir = tmp_path / "outputs" / "projects" / "test-song" / "iterations" / "v001"
        iter_dir.mkdir(parents=True)
        (iter_dir / "full.mid").touch()

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["rate", str(iter_dir), "--rater", "test_user"],
            input="7\n8\n6\n7\n7.5\nGreat piece!\n",
        )

        assert result.exit_code == 0
        assert "Saved to" in result.output

    def test_rate_validates_range(self, tmp_path: Path) -> None:
        """yao rate should reject values outside 1-10."""
        iter_dir = tmp_path / "v001"
        iter_dir.mkdir()

        runner = CliRunner()
        # Enter 0 (rejected), then 7 for each
        result = runner.invoke(
            cli,
            ["rate", str(iter_dir), "--rater", "test"],
            input="0\n7\n7\n7\n7\n7\nnotes\n",
        )

        assert "between 1 and 10" in result.output


class TestReflectIngest:
    """Tests for yao reflect ingest."""

    def test_ingest_creates_profile(self, tmp_path: Path) -> None:
        """yao reflect ingest should create a UserStyleProfile."""
        # Create a rating file
        ratings_dir = tmp_path / "ratings"
        ratings_dir.mkdir()
        rating = {
            "project": "test",
            "iteration": "v001",
            "rater_id": "alice",
            "date": "2026-05-03",
            "memorability": 8.0,
            "emotional_fit": 7.0,
            "technical_quality": 9.0,
            "genre_fitness": 7.5,
            "overall": 8.0,
            "notes": "Good",
        }
        with open(ratings_dir / "test-v001-alice-2026-05-03.json", "w") as f:
            json.dump(rating, f)

        profile_path = tmp_path / "profile.json"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["reflect", "ingest", str(ratings_dir), "--profile-path", str(profile_path)],
        )

        assert result.exit_code == 0
        assert profile_path.exists()
        assert "Ingested 1 rating file" in result.output

        # Verify profile content
        with open(profile_path) as f:
            profile_data = json.load(f)
        assert profile_data["user_id"] == "local"

    def test_ingest_multiple_ratings(self, tmp_path: Path) -> None:
        """Multiple rating files should aggregate into preferences."""
        ratings_dir = tmp_path / "ratings"
        ratings_dir.mkdir()

        for i, overall in enumerate([6.0, 8.0, 7.0]):
            rating = {
                "overall": overall,
                "memorability": overall - 1,
                "emotional_fit": overall,
                "technical_quality": overall + 0.5,
                "genre_fitness": overall,
                "rater_id": f"rater_{i}",
                "date": "2026-05-03",
            }
            with open(ratings_dir / f"test-v001-rater{i}.json", "w") as f:
                json.dump(rating, f)

        profile_path = tmp_path / "profile.json"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["reflect", "ingest", str(ratings_dir), "--profile-path", str(profile_path)],
        )

        assert result.exit_code == 0
        assert "Ingested 3 rating file" in result.output
        assert "overall" in result.output
