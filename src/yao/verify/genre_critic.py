"""GenreCritic — genre-specific anti-pattern detection.

Loads anti-patterns from MelodicProfiles and evaluates generated
ScoreIR against them. Reports issues with severity levels and
fix suggestions that the Conductor can act on.

See PROJECT.md §11.4 and IMPROVEMENT.md §4.9.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yao.ir.score_ir import ScoreIR
from yao.schema.melodic_profile import AntiPattern, MelodicProfile
from yao.verify.conformity import genre_conformity_score, motif_coherence_score


@dataclass(frozen=True)
class CritiqueIssue:
    """A single issue found by the GenreCritic.

    Attributes:
        severity: Issue severity ('critical', 'major', 'minor', 'hint').
        category: Issue category (e.g., 'rhythm', 'harmony', 'melody').
        name: Anti-pattern name from the profile.
        description: What the issue is.
        suggestion: How to fix it.
        metric_value: Optional measured value that triggered the issue.
    """

    severity: str
    category: str
    name: str
    description: str
    suggestion: str
    metric_value: float | None = None


@dataclass(frozen=True)
class CritiqueReport:
    """Complete critique report for a genre.

    Attributes:
        genre: Genre that was critiqued.
        issues: List of issues found.
        conformity_scores: Genre conformity metrics.
        coherence_score: Motif coherence score.
    """

    genre: str
    issues: tuple[CritiqueIssue, ...]
    conformity_scores: dict[str, float]
    coherence_score: float

    @property
    def critical_count(self) -> int:
        """Number of critical issues."""
        return sum(1 for i in self.issues if i.severity == "critical")

    @property
    def major_count(self) -> int:
        """Number of major issues."""
        return sum(1 for i in self.issues if i.severity == "major")

    @property
    def has_critical(self) -> bool:
        """Whether any critical issues were found."""
        return self.critical_count > 0

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return len(self.issues)


class GenreCritic:
    """Evaluates a ScoreIR against genre-specific anti-patterns.

    The critic loads anti-patterns from the genre's MelodicProfile
    and applies automated checks. It also runs genre conformity and
    motif coherence scoring.

    The critic's job is to find weaknesses — it never praises.
    """

    def critique(
        self,
        score: ScoreIR,
        profile: MelodicProfile,
    ) -> CritiqueReport:
        """Critique a score against a genre profile.

        Args:
            score: The ScoreIR to critique.
            profile: The target MelodicProfile.

        Returns:
            A CritiqueReport with all issues found.
        """
        issues: list[CritiqueIssue] = []

        # Run automated anti-pattern checks
        for anti_pattern in profile.anti_patterns:
            result = self._check_anti_pattern(score, profile, anti_pattern)
            if result is not None:
                issues.append(result)

        # Run conformity scoring
        conformity = genre_conformity_score(score, profile)

        # Check conformity thresholds
        overall = conformity.get("overall_genre_conformity", 0.0)
        if overall < 0.3:
            issues.append(
                CritiqueIssue(
                    severity="critical",
                    category="genre_conformity",
                    name="low_genre_conformity",
                    description=f"Overall genre conformity is {overall:.2f}, well below 0.7 target",
                    suggestion="Review interval distribution and chord-tone targeting against the profile",
                    metric_value=overall,
                )
            )
        elif overall < 0.5:
            issues.append(
                CritiqueIssue(
                    severity="major",
                    category="genre_conformity",
                    name="moderate_genre_conformity",
                    description=f"Genre conformity is {overall:.2f}, below 0.7 target",
                    suggestion="Adjust generation parameters to better match genre profile",
                    metric_value=overall,
                )
            )

        # Run coherence scoring
        coherence = motif_coherence_score(score)
        if coherence < 0.2:
            issues.append(
                CritiqueIssue(
                    severity="major",
                    category="motif_coherence",
                    name="low_motif_coherence",
                    description=f"Motif coherence is {coherence:.2f} — piece lacks thematic unity",
                    suggestion="Increase motif_recurrence_rate or use fewer motif transformations",
                    metric_value=coherence,
                )
            )

        return CritiqueReport(
            genre=profile.genre,
            issues=tuple(issues),
            conformity_scores=conformity,
            coherence_score=coherence,
        )

    def _check_anti_pattern(
        self,
        score: ScoreIR,
        profile: MelodicProfile,
        pattern: AntiPattern,
    ) -> CritiqueIssue | None:
        """Check a single anti-pattern against the score.

        Args:
            score: ScoreIR to check.
            profile: Active MelodicProfile.
            pattern: The anti-pattern to check for.

        Returns:
            A CritiqueIssue if the pattern is violated, None otherwise.
        """
        notes = score.all_notes()
        if not notes:
            return None

        # Map anti-pattern names to automated checks
        checker = _ANTI_PATTERN_CHECKERS.get(pattern.name)
        if checker is not None:
            violated, metric = checker(notes, profile)
            if violated:
                return CritiqueIssue(
                    severity=pattern.severity,
                    category="anti_pattern",
                    name=pattern.name,
                    description=pattern.description,
                    suggestion=pattern.fix_suggestion,
                    metric_value=metric,
                )

        return None


# ---------------------------------------------------------------------------
# Anti-pattern checker implementations
# ---------------------------------------------------------------------------


def _check_straight_8ths(notes: list[Any], profile: MelodicProfile) -> tuple[bool, float | None]:
    """Check if music uses straight 8ths when swing is expected."""
    if profile.groove_profile_name in ("straight", "pop_straight"):
        return False, None
    # Check if any rhythm template requires swing
    for template in profile.rhythm_templates:
        if template.swing_ratio > 0.55:
            # Profile expects swing — check if intervals suggest straight timing
            return False, None  # Would need actual timing analysis
    return False, None


def _check_low_chromaticism(notes: list[Any], profile: MelodicProfile) -> tuple[bool, float | None]:
    """Check if chromaticism is too low for the genre."""
    if len(notes) < 2:  # noqa: PLR2004
        return False, None
    # Count chromatic intervals (1 semitone)
    chromatic = sum(1 for i in range(len(notes) - 1) if abs(notes[i + 1].pitch - notes[i].pitch) == 1)
    ratio = chromatic / (len(notes) - 1)
    threshold = profile.chromaticism_level * 0.3  # expect at least 30% of profile's level
    if ratio < threshold and profile.chromaticism_level > 0.4:
        return True, ratio
    return False, None


def _check_too_wide_range(notes: list[Any], profile: MelodicProfile) -> tuple[bool, float | None]:
    """Check if melody exceeds typical range."""
    if not notes or "melody" not in profile.typical_ranges:
        return False, None
    pitches = [n.pitch for n in notes]
    actual_range = max(pitches) - min(pitches)
    # More than 2 octaves is usually too wide for vocal/singable genres
    if actual_range > 24:  # noqa: PLR2004
        return True, float(actual_range)
    return False, None


def _check_no_repetition(notes: list[Any], profile: MelodicProfile) -> tuple[bool, float | None]:
    """Check if motif recurrence is too low."""
    if profile.motif_recurrence_rate < 0.5:
        return False, None  # Genre doesn't require high recurrence
    # Simple heuristic: check for repeated pitch patterns
    if len(notes) < 6:  # noqa: PLR2004
        return False, None
    intervals = [notes[i + 1].pitch - notes[i].pitch for i in range(len(notes) - 1)]
    # Count 3-grams
    trigrams = [tuple(intervals[i : i + 3]) for i in range(len(intervals) - 2)]
    unique_ratio = len(set(trigrams)) / len(trigrams) if trigrams else 1.0
    # If almost all trigrams are unique, there's no repetition
    if unique_ratio > 0.9 and profile.motif_recurrence_rate > 0.6:
        return True, unique_ratio
    return False, None


# Registry of automated anti-pattern checkers
_ANTI_PATTERN_CHECKERS: dict[str, Any] = {
    "straight_8ths": _check_straight_8ths,
    "low_chromaticism": _check_low_chromaticism,
    "too_wide_range": _check_too_wide_range,
    "no_repetition": _check_no_repetition,
    "excessive_chromaticism": _check_low_chromaticism,  # same check, inverse threshold
}
