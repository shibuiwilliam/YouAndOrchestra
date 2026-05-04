"""Curriculum learning — failure-pattern dictionary for Conductor adaptation.

Maintains a persistent dictionary of failure patterns encountered across
all projects. When the Conductor detects a similar problem to one previously
solved, it consults past successful adaptations.

This is non-LLM curriculum learning: patterns are matched by rule_id and
genre, and successful fixes are ranked by their improvement delta.

Belongs to Layer 2 (Conductor subsystem).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

_DEFAULT_CURRICULUM_PATH = Path("outputs/curriculum.json")


@dataclass(frozen=True)
class FailurePattern:
    """A recorded failure pattern with its successful adaptation.

    Attributes:
        rule_id: Critique rule that fired (e.g. "structure.climax_absence").
        genre: Genre context where the failure occurred.
        severity: Severity of the finding.
        adaptation_applied: Description of the adaptation that fixed it.
        adaptation_params: Parameters of the successful fix.
        improvement_delta: How much quality_score improved after the fix.
        occurrence_count: Number of times this pattern has been seen.
    """

    rule_id: str
    genre: str
    severity: str
    adaptation_applied: str
    adaptation_params: dict[str, Any]
    improvement_delta: float
    occurrence_count: int = 1


@dataclass
class CurriculumDictionary:
    """Persistent dictionary of failure patterns and successful adaptations.

    Patterns are keyed by (rule_id, genre) and ranked by improvement_delta.
    """

    patterns: dict[str, FailurePattern] = field(default_factory=dict)

    @staticmethod
    def _key(rule_id: str, genre: str) -> str:
        """Generate a lookup key from rule_id and genre."""
        return f"{rule_id}::{genre}"

    def record_failure(
        self,
        *,
        rule_id: str,
        genre: str,
        severity: str,
        adaptation_applied: str,
        adaptation_params: dict[str, Any],
        improvement_delta: float,
    ) -> None:
        """Record a failure pattern and its successful adaptation.

        If the pattern already exists, update it if the new adaptation
        produced a better improvement. Increment occurrence count.

        Args:
            rule_id: The critique rule that fired.
            genre: Genre context.
            severity: Finding severity.
            adaptation_applied: What adaptation was applied.
            adaptation_params: Parameters of the adaptation.
            improvement_delta: Quality score improvement (positive = better).
        """
        key = self._key(rule_id, genre)
        existing = self.patterns.get(key)

        if existing is None or improvement_delta > existing.improvement_delta:
            count = (existing.occurrence_count + 1) if existing else 1
            self.patterns[key] = FailurePattern(
                rule_id=rule_id,
                genre=genre,
                severity=severity,
                adaptation_applied=adaptation_applied,
                adaptation_params=adaptation_params,
                improvement_delta=improvement_delta,
                occurrence_count=count,
            )
        elif existing is not None:
            # Update occurrence count even if adaptation isn't better
            self.patterns[key] = FailurePattern(
                rule_id=existing.rule_id,
                genre=existing.genre,
                severity=existing.severity,
                adaptation_applied=existing.adaptation_applied,
                adaptation_params=existing.adaptation_params,
                improvement_delta=existing.improvement_delta,
                occurrence_count=existing.occurrence_count + 1,
            )

    def lookup(self, rule_id: str, genre: str) -> FailurePattern | None:
        """Look up a known adaptation for a failure pattern.

        Args:
            rule_id: The critique rule that fired.
            genre: Genre context.

        Returns:
            Best known adaptation, or None if pattern is new.
        """
        key = self._key(rule_id, genre)
        pattern = self.patterns.get(key)
        if pattern is not None:
            return pattern

        # Fallback: try genre-agnostic pattern
        generic_key = self._key(rule_id, "*")
        return self.patterns.get(generic_key)

    def most_frequent_failures(self, n: int = 10) -> list[FailurePattern]:
        """Return the most frequently occurring failure patterns.

        Args:
            n: Number of patterns to return.

        Returns:
            Top-N patterns sorted by occurrence count descending.
        """
        return sorted(
            self.patterns.values(),
            key=lambda p: p.occurrence_count,
            reverse=True,
        )[:n]

    def save(self, path: Path | None = None) -> None:
        """Persist the curriculum dictionary to JSON.

        Args:
            path: Output file path. Defaults to outputs/curriculum.json.
        """
        if path is None:
            path = _DEFAULT_CURRICULUM_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(p) for p in self.patterns.values()]
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path | None = None) -> CurriculumDictionary:
        """Load a curriculum dictionary from JSON.

        Args:
            path: Input file path. Defaults to outputs/curriculum.json.

        Returns:
            CurriculumDictionary instance. Empty if file doesn't exist.
        """
        if path is None:
            path = _DEFAULT_CURRICULUM_PATH
        if not path.exists():
            return cls()

        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("curriculum_load_error", path=str(path))
            return cls()

        curriculum = cls()
        for entry in data:
            pattern = FailurePattern(**entry)
            key = cls._key(pattern.rule_id, pattern.genre)
            curriculum.patterns[key] = pattern
        return curriculum
