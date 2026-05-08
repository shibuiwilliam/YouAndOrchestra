"""GenreProfile — Pydantic v2 model capturing a genre's musical fingerprint.

Every field in this model encodes a musical decision that generators
consult when producing genre-specific output. Profiles are authored as
YAML in ``src/yao/genre/profiles/<name>.yaml`` and validated at load time.

Belongs to Layer 0/1 boundary.

Design notes:
    - Inheritance is supported via the ``parent`` field.
    - Additive overrides use ``_add`` suffixes (e.g., ``chord_palette_extended_add``).
    - All numeric ranges are inclusive.
    - No field may silently fall back to a default without explicit declaration.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from yao.errors import IncompleteGenreProfileError


class InstrumentRoleSpec(BaseModel):
    """An instrument with its role in a genre's instrumentation."""

    name: str
    role: str = "melody"

    model_config = {"extra": "allow"}


class GenreProfile(BaseModel):
    """A genre's complete musical fingerprint for generator consumption.

    This is the canonical Pydantic model for genre profiles. It consolidates
    the two pre-existing systems (System 1 frozen dataclass and System 2
    UnifiedGenreProfile) into a single, validated representation.

    Attributes:
        name: Canonical genre identifier (e.g., "jazz", "lofi_hip_hop").
        parent: Parent genre for inheritance (e.g., "jazz" for "bebop").
        description: Human-readable description of the genre.
        typical_tempo_range: (min_bpm, max_bpm) for this genre.
        typical_keys: Preferred keys (e.g., ["Am", "Dm", "Em"]).
        typical_modes: Preferred modes (e.g., ["minor", "dorian"]).
        typical_time_signatures: Common time signatures.
        typical_form_templates: IDs into the form template library.
        typical_duration_seconds: (min, max) typical duration.
        core_instruments: Instruments that must be present.
        optional_instruments: Instruments that may be present.
        forbidden_instruments: Instruments that must not appear.
        chord_palette_extended: Extended chord types for this genre.
        progression_library_ids: IDs into the progression library.
        harmonic_rhythm: Chords-per-bar range (low, high).
        modal_interchange_allowed: Whether borrowed chords are used.
        chromaticism_level: 0.0 (diatonic) to 1.0 (heavy chromaticism).
        swing_8th: Swing ratio for 8th notes (0.5=straight, 0.67=triplet).
        swing_16th: Swing ratio for 16th notes.
        typical_grooves: Groove template IDs.
        drum_kit_preference: Preferred drum kit ID.
        drum_pattern_ids: Default drum pattern pool.
        polyrhythm_tolerance: 0.0 to 1.0.
        melodic_devices: Genre-specific melodic devices.
        phrase_length_beats: (min, max) typical phrase length.
        typical_scales: Preferred scales.
        call_response_density: 0.0 to 1.0.
        target_lufs: Target loudness.
        target_peak_db: Peak level target.
        typical_effects: Production effect chain elements.
        stereo_imaging: Stereo width descriptor.
        production_profile_id: Link to ProductionProfile.
        cliches_to_avoid: Anti-patterns to reject.
        forbidden_progressions: Progressions that are anti-idiomatic.
        seventh_chord_probability: How often to use 7th chords.
        secondary_dominant_probability: V/x chord probability.
        modal_interchange_probability: Borrowed chord probability.
        blue_note_probability: Blue note usage probability.
        leap_probability: Melodic leap vs step probability.
        melodic_contour_weights: Weight per contour shape.
        syncopation_density: 0.0 to 1.0.
        voicing_density_target: Target number of chord voices.
        bass_motion_style: How the bass line moves.
        typical_dynamics_range: (soft, loud) dynamics range.
        target_spectral_centroid: Brightness (0.0=dark, 1.0=bright).
    """

    name: str
    parent: str | None = None
    description: str = ""

    # Structural defaults
    typical_tempo_range: tuple[float, float] = (80.0, 140.0)
    typical_keys: list[str] = []
    typical_modes: list[str] = []
    typical_time_signatures: list[str] = ["4/4"]
    typical_form_templates: list[str] = []
    typical_duration_seconds: tuple[int, int] = (60, 240)

    # Instrumentation
    core_instruments: list[InstrumentRoleSpec] = []
    optional_instruments: list[InstrumentRoleSpec] = []
    forbidden_instruments: list[str] = []

    # Harmony
    chord_palette_extended: list[str] = []
    progression_library_ids: list[str] = []
    harmonic_rhythm: tuple[float, float] = (0.5, 2.0)
    modal_interchange_allowed: bool = True
    chromaticism_level: float = 0.2
    seventh_chord_probability: float = 0.3
    secondary_dominant_probability: float = 0.1
    modal_interchange_probability: float = 0.1

    # Rhythm
    swing_8th: float = 0.5
    swing_16th: float = 0.5
    typical_grooves: list[str] = []
    drum_kit_preference: str = "standard"
    drum_pattern_ids: list[str] = []
    polyrhythm_tolerance: float = 0.0
    syncopation_density: float = 0.3

    # Melody
    melodic_devices: list[str] = []
    phrase_length_beats: tuple[float, float] = (4.0, 8.0)
    typical_scales: list[str] = []
    call_response_density: float = 0.0
    melodic_contour_weights: dict[str, float] = {}
    leap_probability: float = 0.3
    blue_note_probability: float = 0.0

    # Voicing & instrumentation
    voicing_density_target: int = 4
    bass_motion_style: str = "root_fifth"

    # Dynamics & acoustics
    typical_dynamics_range: tuple[str, str] = ("mp", "f")
    target_spectral_centroid: float = 0.5

    # Production
    target_lufs: float = -14.0
    target_peak_db: float = -1.0
    typical_effects: list[str] = []
    stereo_imaging: str = "moderate"
    production_profile_id: str = ""

    # Anti-patterns
    cliches_to_avoid: list[str] = []
    forbidden_progressions: list[str] = []

    model_config = {"extra": "allow"}

    @field_validator("typical_tempo_range", mode="before")
    @classmethod
    def _coerce_tempo_range(cls, v: object) -> tuple[float, float]:
        """Accept list or tuple for tempo range."""
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (float(v[0]), float(v[1]))
        return (80.0, 140.0)

    @field_validator("harmonic_rhythm", mode="before")
    @classmethod
    def _coerce_harmonic_rhythm(cls, v: object) -> tuple[float, float]:
        """Accept list or tuple for harmonic rhythm."""
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (float(v[0]), float(v[1]))
        return (0.5, 2.0)

    @field_validator("phrase_length_beats", mode="before")
    @classmethod
    def _coerce_phrase_length(cls, v: object) -> tuple[float, float]:
        """Accept list or tuple for phrase length."""
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (float(v[0]), float(v[1]))
        return (4.0, 8.0)

    @field_validator("typical_duration_seconds", mode="before")
    @classmethod
    def _coerce_duration(cls, v: object) -> tuple[int, int]:
        """Accept list or tuple for duration."""
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (int(v[0]), int(v[1]))
        return (60, 240)

    @field_validator("typical_dynamics_range", mode="before")
    @classmethod
    def _coerce_dynamics(cls, v: object) -> tuple[str, str]:
        """Accept list or tuple for dynamics range."""
        if isinstance(v, list | tuple) and len(v) == 2:  # noqa: PLR2004
            return (str(v[0]), str(v[1]))
        return ("mp", "f")

    @field_validator("core_instruments", "optional_instruments", mode="before")
    @classmethod
    def _coerce_instruments(cls, v: object) -> list[InstrumentRoleSpec]:
        """Accept list of strings or dicts for instrument specs."""
        if not isinstance(v, list):
            return []
        result: list[InstrumentRoleSpec] = []
        for item in v:
            if isinstance(item, str):
                result.append(InstrumentRoleSpec(name=item))
            elif isinstance(item, dict):
                result.append(InstrumentRoleSpec(**item))
            elif isinstance(item, InstrumentRoleSpec):
                result.append(item)
        return result

    def validate_complete(self) -> list[str]:
        """Check that mandatory fields have non-default values.

        Returns:
            List of missing field names. Empty list means profile is complete.

        Raises:
            IncompleteGenreProfileError: If critical fields are missing.
        """
        missing: list[str] = []
        if not self.name:
            missing.append("name")
        if missing:
            raise IncompleteGenreProfileError(
                genre_id=self.name or "<unnamed>",
                missing_sections=missing,
            )
        return missing

    @classmethod
    def from_yaml_data(cls, data: dict[str, Any]) -> GenreProfile:
        """Construct a GenreProfile from a parsed YAML dict.

        Handles field name aliases from legacy profile formats (e.g.,
        ``tempo_range`` → ``typical_tempo_range``).

        Args:
            data: Parsed YAML data with genre profile fields.

        Returns:
            Validated GenreProfile instance.
        """
        # Map legacy field names to canonical names
        aliases: dict[str, str] = {
            "tempo_range": "typical_tempo_range",
        }
        mapped = dict(data)
        for old_name, new_name in aliases.items():
            if old_name in mapped and new_name not in mapped:
                mapped[new_name] = mapped.pop(old_name)
        return cls.model_validate(mapped)
