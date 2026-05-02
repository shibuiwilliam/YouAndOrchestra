"""Conftest for subjective tests — markers and rating helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

RATINGS_DIR = Path("tests/subjective/ratings")

REQUIRED_FIELDS = {
    "overall",
    "memorability",
    "emotional_fit",
    "technical_quality",
    "genre_fitness",
    "rater_id",
    "date",
}


@dataclass(frozen=True)
class Rating:
    """A single human rating of a generated composition."""

    overall: float
    memorability: float
    emotional_fit: float
    technical_quality: float
    genre_fitness: float
    rater_id: str
    date: str


@dataclass(frozen=True)
class RatingFile:
    """A collection of ratings for a template."""

    template_name: str
    ratings: list[Rating]

    @property
    def average_overall(self) -> float:
        """Average overall rating."""
        if not self.ratings:
            return 0.0
        return sum(r.overall for r in self.ratings) / len(self.ratings)


def load_rating_file(path: Path) -> RatingFile:
    """Load a rating JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed RatingFile.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    ratings = [Rating(**r) for r in data["ratings"]]
    return RatingFile(template_name=data["template_name"], ratings=ratings)


def available_rating_files() -> list[Path]:
    """Find all rating files in the ratings directory."""
    if not RATINGS_DIR.exists():
        return []
    return sorted(RATINGS_DIR.glob("*.json"))
