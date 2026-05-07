"""Pydantic models for MelodicProfile — genre-specific melody generation parameters.

A MelodicProfile captures the multi-dimensional constellation of features
that define a genre's melodic identity: interval distributions, phrase lengths,
cadence patterns, ornament profiles, and more.

Belongs to Layer 1 (Specification). Consumed by the phrase-first melody
pipeline (Layer 2) and genre conformity evaluation (Layer 6).

See IMPROVEMENT.md §4.2 and PROJECT.md §3.3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator

from yao.errors import SpecValidationError


class IntervalDistribution(BaseModel):
    """Probability distribution over melodic interval sizes (in semitones).

    Keys are absolute interval sizes in semitones, values are probabilities.
    The distribution need not sum to exactly 1.0; it will be normalized
    at usage time.

    Example (jazz): {0: 0.05, 1: 0.20, 2: 0.25, 3: 0.15, 4: 0.10, ...}
    Example (folk): {0: 0.10, 1: 0.05, 2: 0.45, 3: 0.20, ...}
    """

    distribution: dict[int, float]

    @field_validator("distribution")
    @classmethod
    def distribution_not_empty(cls, v: dict[int, float]) -> dict[int, float]:
        """Validate that the distribution has at least one entry."""
        if not v:
            raise SpecValidationError(
                "IntervalDistribution must have at least one entry",
                field="distribution",
            )
        for key, val in v.items():
            if val < 0:
                raise SpecValidationError(
                    f"Interval probability for {key} must be non-negative, got {val}",
                    field="distribution",
                )
        return v

    def normalized(self) -> dict[int, float]:
        """Return a copy normalized to sum to 1.0."""
        total = sum(self.distribution.values())
        if total <= 0:
            return dict(self.distribution)
        return {k: v / total for k, v in self.distribution.items()}


class RhythmTemplate(BaseModel):
    """A rhythmic pattern template used in surface realization (M3).

    Attributes:
        name: Template identifier (e.g., "swing_8ths", "bossa_comping").
        pattern: Beat positions within a bar where attacks occur.
        durations: Duration of each attack in beats.
        swing_ratio: Swing amount (0.5 = straight, 0.67 = triplet swing).
        syncopation_level: How much syncopation (0.0–1.0).
    """

    name: str
    pattern: list[float] = []
    durations: list[float] = []
    swing_ratio: float = 0.5
    syncopation_level: float = 0.0

    @field_validator("swing_ratio")
    @classmethod
    def swing_ratio_valid(cls, v: float) -> float:
        """Validate swing ratio is in [0.5, 0.75]."""
        if not 0.5 <= v <= 0.75:
            raise SpecValidationError(
                f"swing_ratio must be in [0.5, 0.75], got {v}",
                field="swing_ratio",
            )
        return v


class CadencePattern(BaseModel):
    """A cadential chord pattern with its melodic resolution target.

    Attributes:
        name: Pattern identifier (e.g., "ii-V-I", "PAC").
        chord_sequence: Chord symbols in functional notation.
        melodic_target: Scale degree the melody should land on (e.g., "1", "3", "5").
    """

    name: str
    chord_sequence: list[str]
    melodic_target: str = "1"


class OrnamentProfile(BaseModel):
    """Genre-specific probabilities for ornament application in M4.

    All probabilities are in [0.0, 1.0].

    Attributes:
        grace_note_probability: Likelihood of adding a grace note.
        trill_probability: Likelihood of adding a trill.
        bend_probability: Likelihood of adding a pitch bend.
        slide_probability: Likelihood of adding a slide/glissando.
        mordent_probability: Likelihood of adding a mordent.
        turn_probability: Likelihood of adding a turn.
        ghost_note_probability: Likelihood of adding ghost notes.
        legato_ratio: Proportion of legato articulation.
        staccato_ratio: Proportion of staccato articulation.
        accent_ratio: Proportion of accented notes.
    """

    grace_note_probability: float = 0.0
    trill_probability: float = 0.0
    bend_probability: float = 0.0
    slide_probability: float = 0.0
    mordent_probability: float = 0.0
    turn_probability: float = 0.0
    ghost_note_probability: float = 0.0
    legato_ratio: float = 0.5
    staccato_ratio: float = 0.0
    accent_ratio: float = 0.1

    @field_validator(
        "grace_note_probability",
        "trill_probability",
        "bend_probability",
        "slide_probability",
        "mordent_probability",
        "turn_probability",
        "ghost_note_probability",
        "legato_ratio",
        "staccato_ratio",
        "accent_ratio",
    )
    @classmethod
    def probability_in_range(cls, v: float) -> float:
        """Validate all probability fields are in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Probability must be in [0.0, 1.0], got {v}",
                field="ornament_profile",
            )
        return v


class PhraseLengthDistribution(BaseModel):
    """Distribution over phrase lengths in bars.

    Keys are phrase lengths in bars, values are probabilities.

    Example (classical): {4: 0.50, 8: 0.40, 16: 0.10}
    Example (jazz):      {4: 0.10, 8: 0.40, 12: 0.20, 16: 0.30}
    """

    distribution: dict[int, float]

    @field_validator("distribution")
    @classmethod
    def distribution_valid(cls, v: dict[int, float]) -> dict[int, float]:
        """Validate that phrase lengths are positive and probabilities non-negative."""
        if not v:
            raise SpecValidationError(
                "PhraseLengthDistribution must have at least one entry",
                field="distribution",
            )
        for bars, prob in v.items():
            if bars <= 0:
                raise SpecValidationError(
                    f"Phrase length must be positive, got {bars}",
                    field="distribution",
                )
            if prob < 0:
                raise SpecValidationError(
                    f"Phrase probability must be non-negative, got {prob}",
                    field="distribution",
                )
        return v

    def normalized(self) -> dict[int, float]:
        """Return a copy normalized to sum to 1.0."""
        total = sum(self.distribution.values())
        if total <= 0:
            return dict(self.distribution)
        return {k: v / total for k, v in self.distribution.items()}


class AntiPattern(BaseModel):
    """A genre-specific anti-pattern for the Adversarial Critic.

    Attributes:
        name: Short identifier for the anti-pattern.
        description: What the anti-pattern is and why it's bad for this genre.
        severity: How serious this anti-pattern is.
        fix_suggestion: Actionable advice for fixing it.
    """

    name: str
    description: str
    severity: str = "major"
    fix_suggestion: str = ""

    @field_validator("severity")
    @classmethod
    def severity_valid(cls, v: str) -> str:
        """Validate severity is one of the allowed levels."""
        allowed = {"critical", "major", "minor", "hint"}
        if v not in allowed:
            raise SpecValidationError(
                f"severity must be one of {allowed}, got '{v}'",
                field="severity",
            )
        return v


class MelodicProfile(BaseModel):
    """Genre-specific parameters for melody generation.

    This is the central data structure that parameterizes the phrase-first
    melody pipeline (M1–M4). Every decision in the pipeline — phrase lengths,
    skeleton chord-tone targeting, surface interval selection, ornament
    application — consults the active MelodicProfile.

    See PROJECT.md §3.3 for the full design rationale.
    """

    genre: str
    description: str = ""

    scale_preferences: dict[str, float] = {}
    interval_distribution: IntervalDistribution
    chord_tone_targeting: float = 0.5
    chromaticism_level: float = 0.0
    syncopation_level: float = 0.0
    phrase_length_distribution: PhraseLengthDistribution
    cadence_patterns: list[CadencePattern] = []
    rhythm_templates: list[RhythmTemplate] = []
    ornament_profile: OrnamentProfile = OrnamentProfile()
    typical_ranges: dict[str, tuple[str, str]] = {}
    motif_length_bars: float = 2.0
    motif_recurrence_rate: float = 0.5
    motif_transformations: dict[str, float] = {}
    groove_profile_name: str = "straight"
    anti_patterns: list[AntiPattern] = []

    @field_validator("chord_tone_targeting", "chromaticism_level", "syncopation_level")
    @classmethod
    def unit_float(cls, v: float) -> float:
        """Validate fields that must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Value must be in [0.0, 1.0], got {v}",
                field="melodic_profile",
            )
        return v

    @field_validator("motif_length_bars")
    @classmethod
    def motif_length_positive(cls, v: float) -> float:
        """Validate motif length is positive."""
        if v <= 0:
            raise SpecValidationError(
                f"motif_length_bars must be positive, got {v}",
                field="motif_length_bars",
            )
        return v

    @field_validator("motif_recurrence_rate")
    @classmethod
    def recurrence_rate_valid(cls, v: float) -> float:
        """Validate motif recurrence rate is in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"motif_recurrence_rate must be in [0.0, 1.0], got {v}",
                field="motif_recurrence_rate",
            )
        return v

    @field_validator("typical_ranges", mode="before")
    @classmethod
    def coerce_ranges(cls, v: Any) -> dict[str, tuple[str, str]]:
        """Accept lists or tuples for ranges."""
        if not isinstance(v, dict):
            return dict(v) if v else {}
        result: dict[str, tuple[str, str]] = {}
        for key, val in v.items():
            if isinstance(val, list | tuple) and len(val) == 2:  # noqa: PLR2004
                result[key] = (str(val[0]), str(val[1]))
            else:
                result[key] = val
        return result

    model_config = {"extra": "forbid"}


def load_melodic_profile(genre: str) -> MelodicProfile:
    """Load a MelodicProfile from the constants directory.

    Args:
        genre: Genre identifier matching a YAML filename in
            ``src/yao/constants/melodic_profiles/<genre>.yaml``.

    Returns:
        A validated MelodicProfile instance.

    Raises:
        SpecValidationError: If the file is missing or fails validation.
    """
    profiles_dir = Path(__file__).resolve().parent.parent / "constants" / "melodic_profiles"
    path = profiles_dir / f"{genre}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in profiles_dir.glob("*.yaml")) if profiles_dir.exists() else []
        raise SpecValidationError(
            f"No melodic profile found for genre '{genre}'. Available: {available}",
            field="genre",
        )
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SpecValidationError(
            f"Melodic profile '{genre}' must be a YAML mapping",
            field="genre",
        )
    return MelodicProfile(**data)


def blend_profiles(
    primary: MelodicProfile,
    secondary: MelodicProfile,
    ratio: float,
) -> MelodicProfile:
    """Blend two MelodicProfiles with a weighted ratio.

    Args:
        primary: The dominant profile.
        secondary: The secondary profile to blend in.
        ratio: Weight for the primary profile (0.0–1.0).
            0.7 means 70% primary, 30% secondary.

    Returns:
        A new blended MelodicProfile.
    """
    inv = 1.0 - ratio

    # Blend interval distributions
    all_intervals = set(primary.interval_distribution.distribution) | set(secondary.interval_distribution.distribution)
    blended_intervals = {
        k: ratio * primary.interval_distribution.distribution.get(k, 0.0)
        + inv * secondary.interval_distribution.distribution.get(k, 0.0)
        for k in all_intervals
    }

    # Blend phrase length distributions
    all_lengths = set(primary.phrase_length_distribution.distribution) | set(
        secondary.phrase_length_distribution.distribution
    )
    blended_phrase_lengths = {
        k: ratio * primary.phrase_length_distribution.distribution.get(k, 0.0)
        + inv * secondary.phrase_length_distribution.distribution.get(k, 0.0)
        for k in all_lengths
    }

    # Blend scale preferences
    all_scales = set(primary.scale_preferences) | set(secondary.scale_preferences)
    blended_scales = {
        k: ratio * primary.scale_preferences.get(k, 0.0) + inv * secondary.scale_preferences.get(k, 0.0)
        for k in all_scales
    }

    # Blend motif transformations
    all_transforms = set(primary.motif_transformations) | set(secondary.motif_transformations)
    blended_transforms = {
        k: ratio * primary.motif_transformations.get(k, 0.0) + inv * secondary.motif_transformations.get(k, 0.0)
        for k in all_transforms
    }

    return MelodicProfile(
        genre=f"{primary.genre}_x_{secondary.genre}",
        description=f"Blend of {primary.genre} ({ratio:.0%}) and {secondary.genre} ({inv:.0%})",
        scale_preferences=blended_scales,
        interval_distribution=IntervalDistribution(distribution=blended_intervals),
        chord_tone_targeting=ratio * primary.chord_tone_targeting + inv * secondary.chord_tone_targeting,
        chromaticism_level=ratio * primary.chromaticism_level + inv * secondary.chromaticism_level,
        syncopation_level=ratio * primary.syncopation_level + inv * secondary.syncopation_level,
        phrase_length_distribution=PhraseLengthDistribution(distribution=blended_phrase_lengths),
        cadence_patterns=primary.cadence_patterns,
        rhythm_templates=primary.rhythm_templates,
        ornament_profile=OrnamentProfile(
            grace_note_probability=ratio * primary.ornament_profile.grace_note_probability
            + inv * secondary.ornament_profile.grace_note_probability,
            trill_probability=ratio * primary.ornament_profile.trill_probability
            + inv * secondary.ornament_profile.trill_probability,
            bend_probability=ratio * primary.ornament_profile.bend_probability
            + inv * secondary.ornament_profile.bend_probability,
            slide_probability=ratio * primary.ornament_profile.slide_probability
            + inv * secondary.ornament_profile.slide_probability,
            mordent_probability=ratio * primary.ornament_profile.mordent_probability
            + inv * secondary.ornament_profile.mordent_probability,
            turn_probability=ratio * primary.ornament_profile.turn_probability
            + inv * secondary.ornament_profile.turn_probability,
            ghost_note_probability=ratio * primary.ornament_profile.ghost_note_probability
            + inv * secondary.ornament_profile.ghost_note_probability,
            legato_ratio=ratio * primary.ornament_profile.legato_ratio + inv * secondary.ornament_profile.legato_ratio,
            staccato_ratio=ratio * primary.ornament_profile.staccato_ratio
            + inv * secondary.ornament_profile.staccato_ratio,
            accent_ratio=ratio * primary.ornament_profile.accent_ratio + inv * secondary.ornament_profile.accent_ratio,
        ),
        typical_ranges=primary.typical_ranges,
        motif_length_bars=ratio * primary.motif_length_bars + inv * secondary.motif_length_bars,
        motif_recurrence_rate=ratio * primary.motif_recurrence_rate + inv * secondary.motif_recurrence_rate,
        motif_transformations=blended_transforms,
        groove_profile_name=primary.groove_profile_name,
        anti_patterns=primary.anti_patterns,
    )
