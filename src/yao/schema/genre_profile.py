"""Unified GenreProfile schema — the numeric backbone of genre identity.

Merges two existing genre systems:
- System 1 (constants/genre_profile.py): 18 generator-focused numeric fields
- System 2 (skills/loader.py): 11 spec-focused fields

The unified schema organizes all genre data into themed sections per
PROJECT.md Section 9.1 and supports inheritance via a ``parent`` field.

This is a Pydantic model (Layer 1 schema) consumed by generators (Layer 2)
and evaluators (Layer 6) via adapter functions.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class GenreIdentitySection(BaseModel):
    """Genre identity metadata."""

    name: str = ""
    family: str = ""
    origin: str = ""

    model_config = {"extra": "allow"}


class GenreTempoSection(BaseModel):
    """Tempo range and drift tolerance."""

    central: float | None = None
    range: tuple[float, float] | None = None
    drift_tolerance: float = 0.05

    model_config = {"extra": "allow"}

    @field_validator("range", mode="before")
    @classmethod
    def _coerce_range(cls, v: object) -> tuple[float, float] | None:
        """Accept list or tuple for range."""
        if v is None:
            return None
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (float(v[0]), float(v[1]))
        return None


class GenreMeterSection(BaseModel):
    """Default meter and alternates."""

    default: str = "4/4"
    alternates: list[str] = []

    model_config = {"extra": "allow"}


class GenreTuningSection(BaseModel):
    """Default tuning system."""

    default: str = "12tet"

    model_config = {"extra": "allow"}


class GenreGrooveSection(BaseModel):
    """Groove profile reference and swing parameters."""

    default: str | None = None
    swing_value: float | None = None
    swing_range: tuple[float, float] | None = None

    model_config = {"extra": "allow"}

    @field_validator("swing_range", mode="before")
    @classmethod
    def _coerce_swing_range(cls, v: object) -> tuple[float, float] | None:
        """Accept list or tuple."""
        if v is None:
            return None
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (float(v[0]), float(v[1]))
        return None


class GenreHarmonySection(BaseModel):
    """Harmonic preferences: chord palette, progressions, probabilities."""

    chord_palette: list[str] = []
    progression_n_grams: dict[str, float] = {}
    seventh_chord_probability: float = 0.3
    secondary_dominant_probability: float = 0.1
    modal_interchange_probability: float = 0.1
    preferred_chord_extensions: list[str] = []
    modulation_frequency: float = 0.0
    key_preferences: list[str] = []
    cliche_progressions_to_avoid: list[str] = []
    signature_progressions: list[str] = []
    chord_progressions: list[list[str]] = []

    model_config = {"extra": "allow"}


class GenreMelodySection(BaseModel):
    """Melodic characteristics."""

    melodic_contour_weights: dict[str, float] = {}
    leap_probability: float = 0.3
    blue_note_probability: float = 0.0
    range_octaves: float | None = None
    contour: list[str] = []
    syncopation_mean: float | None = None
    pentatonic_bias: float = 0.0

    model_config = {"extra": "allow"}


class GenreDrumsSection(BaseModel):
    """Drum pattern and rhythmic defaults."""

    default_pattern: str | None = None
    kick_density_mean: float | None = None
    kick_density_range: tuple[float, float] | None = None
    snare_position: list[str] = []
    ghost_notes: float = 0.0
    swing_ratio: float = 0.5
    syncopation_density: float = 0.3
    rhythm_template_weights: dict[str, float] = {}
    characteristic_rhythms: list[str] = []

    model_config = {"extra": "allow"}

    @field_validator("kick_density_range", mode="before")
    @classmethod
    def _coerce_range(cls, v: object) -> tuple[float, float] | None:
        """Accept list or tuple."""
        if v is None:
            return None
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (float(v[0]), float(v[1]))
        return None


class GenreInstrumentationSection(BaseModel):
    """Instrument preferences and restrictions."""

    required: list[str] = []
    signature: list[str] = []
    preferred: list[str] = []
    optional: list[str] = []
    forbidden: list[str] = []
    avoided: list[str] = []
    typical_keys: list[str] = []
    modal_options: list[str] = []

    model_config = {"extra": "allow"}


class GenreArticulationSection(BaseModel):
    """Per-instrument articulation defaults."""

    defaults: dict[str, list[str]] = {}

    model_config = {"extra": "allow"}


class GenreProductionSection(BaseModel):
    """Production chain defaults."""

    filter_chain: list[dict[str, Any]] = []
    sidechain: bool = False
    stereo_width: float = 0.5
    bit_reduction_enabled: bool = False
    bit_reduction_depth: int = 16
    target_lufs: float = -14.0

    model_config = {"extra": "allow"}


class GenreEvaluationSection(BaseModel):
    """Evaluation weights and bonus metrics for this genre.

    Weights map dimension names to floats (0.0-1.0).
    If a dimension is missing, the default weight from the evaluator is used.
    """

    weights: dict[str, float] = {}
    bonus_metrics: list[dict[str, Any]] = []
    percussion_centric: bool = False

    model_config = {"extra": "allow"}


class GenreAestheticSection(BaseModel):
    """Genre-specific aesthetic critique rules."""

    rules: list[dict[str, str]] = []

    model_config = {"extra": "allow"}


class UnifiedGenreProfile(BaseModel):
    """Unified genre profile combining all genre data.

    Supports inheritance via the ``parent`` field: when loading,
    the parent's fields are used as defaults and the child's fields
    override them.

    Attributes:
        genre_id: Canonical genre identifier.
        parent: Parent genre ID for inheritance (or None).
        cultural_context: Cultural notes (required for non-Western genres).
        identity: Genre identity metadata.
        tempo: Tempo range and drift tolerance.
        meter: Default meter and alternates.
        tuning: Default tuning system.
        groove: Groove profile reference and swing.
        harmony: Harmonic preferences.
        melody: Melodic characteristics.
        drums: Drum pattern and rhythm defaults.
        instrumentation: Instrument preferences.
        articulation_defaults: Per-instrument articulation.
        production: Production chain defaults.
        evaluation: Evaluation weights for this genre.
        generator_assignments: Per-part generator strategy mapping.
        aesthetic_critique: Genre-specific aesthetic rules.
    """

    genre_id: str
    parent: str | None = None
    cultural_context: str | None = None

    identity: GenreIdentitySection = GenreIdentitySection()
    tempo: GenreTempoSection = GenreTempoSection()
    meter: GenreMeterSection = GenreMeterSection()
    tuning: GenreTuningSection = GenreTuningSection()
    groove: GenreGrooveSection = GenreGrooveSection()
    harmony: GenreHarmonySection = GenreHarmonySection()
    melody: GenreMelodySection = GenreMelodySection()
    drums: GenreDrumsSection = GenreDrumsSection()
    instrumentation: GenreInstrumentationSection = GenreInstrumentationSection()
    articulation_defaults: GenreArticulationSection = GenreArticulationSection()
    production: GenreProductionSection = GenreProductionSection()
    evaluation: GenreEvaluationSection = GenreEvaluationSection()
    generator_assignments: dict[str, str] = {}
    aesthetic_critique: GenreAestheticSection = GenreAestheticSection()

    # Additional fields from existing System 1 that don't fit neatly into sections
    voicing_density_target: int = 4
    bass_motion_style: str = "root_fifth"
    typical_dynamics_range: tuple[str, str] = ("mp", "f")
    target_spectral_centroid: float = 0.5

    model_config = {"extra": "allow"}

    @field_validator("typical_dynamics_range", mode="before")
    @classmethod
    def _coerce_dynamics(cls, v: object) -> tuple[str, str]:
        """Accept list or tuple for dynamics range."""
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (str(v[0]), str(v[1]))
        if isinstance(v, tuple) and len(v) == 2:  # noqa: PLR2004
            return (str(v[0]), str(v[1]))
        return ("mp", "f")

    def validate_complete(self) -> None:
        """Check that mandatory sections have non-default values.

        Raises:
            IncompleteGenreProfileError: If required sections are missing data.
        """
        from yao.errors import IncompleteGenreProfileError

        missing: list[str] = []
        if not self.identity.name:
            missing.append("identity.name")
        if self.tempo.range is None:
            missing.append("tempo.range")
        if missing:
            raise IncompleteGenreProfileError(
                genre_id=self.genre_id,
                missing_sections=missing,
            )
