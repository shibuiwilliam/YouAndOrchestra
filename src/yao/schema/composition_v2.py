"""Pydantic models for composition.yaml v2 specification.

The v2 schema organizes a composition into 11 named sections:
identity, global, emotion, form, melody, harmony, rhythm, drums,
arrangement, production, constraints — plus a generation config.

This is an additive evolution of v1. The v1 schema remains in
composition.py for backward compatibility.

Belongs to Layer 1 (Specification).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from yao.constants.music import DYNAMICS_TO_VELOCITY, SCALE_INTERVALS
from yao.errors import SpecValidationError
from yao.ir.notation import note_name_to_midi

# ---------------------------------------------------------------------------
# Sub-specs
# ---------------------------------------------------------------------------


class IdentitySpec(BaseModel):
    """Who this piece is and what it's for.

    Attributes:
        title: Human-readable title.
        purpose: Short description of use (e.g., "product demo bgm").
        duration_sec: Target duration in seconds.
        loopable: Whether the piece should loop seamlessly.
    """

    title: str
    purpose: str = ""
    duration_sec: float = 120.0
    loopable: bool = False

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Title must be non-empty."""
        if not v.strip():
            raise SpecValidationError("Title cannot be empty", field="identity.title")
        return v.strip()

    @field_validator("duration_sec")
    @classmethod
    def duration_positive(cls, v: float) -> float:
        """Duration must be positive."""
        if v <= 0:
            raise SpecValidationError(
                f"Duration must be positive, got {v}",
                field="identity.duration_sec",
            )
        return v


class GlobalSpec(BaseModel):
    """Global musical parameters.

    Attributes:
        key: Key signature (e.g., "D major").
        bpm: Tempo in beats per minute.
        time_signature: Time signature (e.g., "4/4").
        genre: Genre tag (e.g., "future_pop").
    """

    key: str = "C major"
    bpm: float = 120.0
    time_signature: str = "4/4"
    genre: str = "general"

    @field_validator("key")
    @classmethod
    def key_valid(cls, v: str) -> str:
        """Key must be 'Note Scale' with a known scale type."""
        parts = v.split()
        if len(parts) != 2:  # noqa: PLR2004
            raise SpecValidationError(
                f"Key must be 'Note Scale' (e.g., 'C major'), got '{v}'",
                field="global.key",
            )
        if parts[1] not in SCALE_INTERVALS:
            raise SpecValidationError(
                f"Unknown scale type '{parts[1]}'. Valid: {list(SCALE_INTERVALS.keys())}",
                field="global.key",
            )
        return v

    @field_validator("bpm")
    @classmethod
    def bpm_reasonable(cls, v: float) -> float:
        """BPM must be between 20 and 300."""
        if not 20.0 <= v <= 300.0:
            raise SpecValidationError(
                f"BPM must be between 20 and 300, got {v}",
                field="global.bpm",
            )
        return v

    @field_validator("time_signature")
    @classmethod
    def time_signature_valid(cls, v: str) -> str:
        """Time signature must be 'N/D' with positive integers."""
        parts = v.split("/")
        if len(parts) != 2:  # noqa: PLR2004
            raise SpecValidationError(
                f"Time signature must be 'N/D' (e.g., '4/4'), got '{v}'",
                field="global.time_signature",
            )
        try:
            num, den = int(parts[0]), int(parts[1])
        except ValueError as e:
            raise SpecValidationError(
                f"Invalid time signature '{v}'", field="global.time_signature"
            ) from e
        if num <= 0 or den <= 0:
            raise SpecValidationError(
                f"Time signature components must be positive, got '{v}'",
                field="global.time_signature",
            )
        return v


class EmotionSpec(BaseModel):
    """Emotional profile of the piece. All values in [0.0, 1.0].

    Attributes:
        valence: Bright (1.0) to dark (0.0).
        energy: High energy (1.0) to calm (0.0).
        tension: High tension (1.0) to relaxed (0.0).
        warmth: Warm (1.0) to cold (0.0).
        nostalgia: Nostalgic (1.0) to present-focused (0.0).
    """

    valence: float = 0.5
    energy: float = 0.5
    tension: float = 0.5
    warmth: float = 0.5
    nostalgia: float = 0.3

    @model_validator(mode="after")
    def all_in_unit_range(self) -> EmotionSpec:
        """All emotion values must be in [0.0, 1.0]."""
        for name in ("valence", "energy", "tension", "warmth", "nostalgia"):
            val = getattr(self, name)
            if not 0.0 <= val <= 1.0:
                raise SpecValidationError(
                    f"emotion.{name} must be 0.0–1.0, got {val}",
                    field=f"emotion.{name}",
                )
        return self


class SectionFormSpec(BaseModel):
    """A single section in the song form.

    Attributes:
        id: Section identifier (e.g., "intro", "verse", "chorus").
        bars: Number of bars.
        density: Target note density (0.0–1.0).
        dynamics: Dynamic marking (default from global).
        climax: Whether this section is the climax.
    """

    id: str
    bars: int
    density: float = 0.5
    dynamics: str | None = None
    climax: bool = False

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        """Section id must be non-empty."""
        if not v.strip():
            raise SpecValidationError("Section id cannot be empty", field="form.sections.id")
        return v.strip()

    @field_validator("bars")
    @classmethod
    def bars_positive(cls, v: int) -> int:
        """Section bars must be positive."""
        if v <= 0:
            raise SpecValidationError(
                f"Section bars must be positive, got {v}",
                field="form.sections.bars",
            )
        return v

    @field_validator("density")
    @classmethod
    def density_in_range(cls, v: float) -> float:
        """Density must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Section density must be 0.0–1.0, got {v}",
                field="form.sections.density",
            )
        return v

    @field_validator("dynamics")
    @classmethod
    def dynamics_valid(cls, v: str | None) -> str | None:
        """Dynamics must be a valid marking if provided."""
        if v is not None and v not in DYNAMICS_TO_VELOCITY:
            raise SpecValidationError(
                f"Unknown dynamics '{v}'. Valid: {list(DYNAMICS_TO_VELOCITY.keys())}",
                field="form.sections.dynamics",
            )
        return v


class FormSpec(BaseModel):
    """Song form — section structure.

    Attributes:
        sections: Ordered list of sections.
    """

    sections: list[SectionFormSpec]

    @field_validator("sections")
    @classmethod
    def sections_not_empty(cls, v: list[SectionFormSpec]) -> list[SectionFormSpec]:
        """At least one section is required."""
        if not v:
            raise SpecValidationError("At least one section is required", field="form.sections")
        return v

    @model_validator(mode="after")
    def unique_section_ids(self) -> FormSpec:
        """Section ids must be unique."""
        ids = [s.id for s in self.sections]
        dupes = [i for i in ids if ids.count(i) > 1]
        if dupes:
            raise SpecValidationError(
                f"Duplicate section ids: {set(dupes)}",
                field="form.sections",
            )
        return self

    @model_validator(mode="after")
    def at_most_one_climax(self) -> FormSpec:
        """At most one section can be the climax."""
        climax_ids = [s.id for s in self.sections if s.climax]
        if len(climax_ids) > 1:
            raise SpecValidationError(
                f"Multiple climax sections: {climax_ids}. At most one allowed.",
                field="form.sections",
            )
        return self


class NoteRangeSpec(BaseModel):
    """Note range with min and max in scientific pitch notation.

    Attributes:
        min: Lowest note (e.g., "A3").
        max: Highest note (e.g., "E5").
    """

    min: str
    max: str

    @model_validator(mode="after")
    def min_below_max(self) -> NoteRangeSpec:
        """Min note must be below max note."""
        try:
            min_midi = note_name_to_midi(self.min)
            max_midi = note_name_to_midi(self.max)
        except SpecValidationError:
            # Individual note validation errors are already clear
            return self
        if min_midi >= max_midi:
            raise SpecValidationError(
                f"melody.range.min ({self.min}={min_midi}) must be below "
                f"melody.range.max ({self.max}={max_midi})",
                field="melody.range",
            )
        return self


class MotifSpec(BaseModel):
    """Motif generation parameters.

    Attributes:
        length_beats: Length of seed motif in beats.
        repetition_rate: How often the motif repeats (0.0–1.0).
        variation_rate: How much the motif varies on repetition (0.0–1.0).
    """

    length_beats: float = 2.0
    repetition_rate: float = 0.5
    variation_rate: float = 0.3

    @field_validator("repetition_rate", "variation_rate")
    @classmethod
    def rate_in_range(cls, v: float) -> float:
        """Rates must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Rate must be 0.0–1.0, got {v}",
                field="melody.motif",
            )
        return v


class IntervalSpec(BaseModel):
    """Interval constraints for melody generation.

    Attributes:
        stepwise_ratio: Target ratio of stepwise motion (0.0–1.0).
        max_leap: Maximum allowed interval as abbreviated name (e.g., "P5", "M6").
    """

    stepwise_ratio: float = 0.7
    max_leap: str = "P5"

    @field_validator("stepwise_ratio")
    @classmethod
    def ratio_in_range(cls, v: float) -> float:
        """Stepwise ratio must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"stepwise_ratio must be 0.0–1.0, got {v}",
                field="melody.intervals.stepwise_ratio",
            )
        return v


class PhraseSpec(BaseModel):
    """Phrase structure parameters.

    Attributes:
        bars_per_phrase: Number of bars per phrase.
        call_response: Whether to use call-and-response phrasing.
    """

    bars_per_phrase: float = 4.0
    call_response: bool = False


class MelodySpec(BaseModel):
    """Melody generation parameters.

    Attributes:
        range: Note range (min/max).
        contour: Melodic contour shape.
        motif: Motif generation parameters.
        intervals: Interval constraints.
        phrase: Phrase structure parameters.
    """

    range: NoteRangeSpec | None = None
    contour: str = "arch"
    motif: MotifSpec = Field(default_factory=MotifSpec)
    intervals: IntervalSpec = Field(default_factory=IntervalSpec)
    phrase: PhraseSpec = Field(default_factory=PhraseSpec)


class CadenceMap(BaseModel, extra="allow"):
    """Maps section ids to cadence types.

    Uses extra="allow" so any section name can be a key.
    Cadence values are strings like "half", "authentic", "plagal", "deceptive".
    """

    def section_cadences(self) -> dict[str, str]:
        """Return all section → cadence mappings."""
        # model_extra contains the dynamically-added fields
        result: dict[str, str] = {}
        if self.model_extra:
            for k, v in self.model_extra.items():
                if isinstance(v, str):
                    result[k] = v
        return result


class HarmonicRhythmMap(BaseModel, extra="allow"):
    """Maps section ids to harmonic rhythm descriptions.

    Uses extra="allow" so any section name can be a key.
    """

    def section_rhythms(self) -> dict[str, str]:
        """Return all section → harmonic rhythm mappings."""
        result: dict[str, str] = {}
        if self.model_extra:
            for k, v in self.model_extra.items():
                if isinstance(v, str):
                    result[k] = v
        return result


class HarmonySpec(BaseModel):
    """Harmony generation parameters.

    Attributes:
        complexity: Harmonic complexity (0.0–1.0).
        chord_palette: Allowed chords as Roman numerals.
        cadence: Section → cadence type mapping.
        harmonic_rhythm: Section → harmonic rhythm description.
    """

    complexity: float = 0.5
    chord_palette: list[str] = Field(default_factory=lambda: ["I", "IV", "V", "vi"])
    cadence: CadenceMap = Field(default_factory=CadenceMap)
    harmonic_rhythm: HarmonicRhythmMap = Field(default_factory=HarmonicRhythmMap)

    @field_validator("complexity")
    @classmethod
    def complexity_in_range(cls, v: float) -> float:
        """Complexity must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"harmony.complexity must be 0.0–1.0, got {v}",
                field="harmony.complexity",
            )
        return v

    @field_validator("chord_palette")
    @classmethod
    def palette_not_empty(cls, v: list[str]) -> list[str]:
        """Chord palette must not be empty."""
        if not v:
            raise SpecValidationError(
                "harmony.chord_palette must have at least one chord",
                field="harmony.chord_palette",
            )
        return v


class RhythmSpec(BaseModel):
    """Rhythm parameters.

    Attributes:
        groove: Groove type (e.g., "four_on_the_floor", "shuffle").
        swing: Swing amount (0.0–1.0).
        syncopation: Syncopation amount (0.0–1.0).
    """

    groove: str = "straight"
    swing: float = 0.0
    syncopation: float = 0.0

    @field_validator("swing", "syncopation")
    @classmethod
    def param_in_range(cls, v: float) -> float:
        """Swing and syncopation must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"rhythm parameter must be 0.0–1.0, got {v}",
                field="rhythm",
            )
        return v


class DrumsSpec(BaseModel):
    """Drum specification — first-class in v2.

    Attributes:
        pattern_family: Drum pattern family (e.g., "pop_8beat").
        swing: Drum-specific swing (0.0–1.0).
        ghost_notes_density: Ghost note density (0.0–1.0).
        fills_at: Section points where fills should occur.
    """

    pattern_family: str = "basic"
    swing: float = 0.0
    ghost_notes_density: float = 0.0
    fills_at: list[str] = Field(default_factory=list)

    @field_validator("swing", "ghost_notes_density")
    @classmethod
    def param_in_range(cls, v: float) -> float:
        """Drum parameters must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"drums parameter must be 0.0–1.0, got {v}",
                field="drums",
            )
        return v


class InstrumentArrangementSpec(BaseModel):
    """Per-instrument arrangement specification.

    Attributes:
        role: Musical role of this instrument.
        pattern_family: Optional pattern family for this instrument.
        motion: Bass motion type (e.g., "root_octave_passing").
        voicing: Voicing style (e.g., "wide", "close").
        articulation: Articulation style (e.g., "pluck", "legato").
    """

    role: Literal["melody", "harmony", "bass", "rhythm", "pad"]
    pattern_family: str | None = None
    motion: str | None = None
    voicing: str | None = None
    articulation: str | None = None


class CounterMelodySpec(BaseModel):
    """Counter-melody configuration.

    Attributes:
        enabled_sections: Section ids where counter-melody is active.
    """

    enabled_sections: list[str] = Field(default_factory=list)


class ArrangementSpecV2(BaseModel):
    """Arrangement specification.

    Attributes:
        instruments: Map of instrument name → arrangement spec.
        counter_melody: Counter-melody configuration.
    """

    instruments: dict[str, InstrumentArrangementSpec] = Field(default_factory=dict)
    counter_melody: CounterMelodySpec = Field(default_factory=CounterMelodySpec)

    @field_validator("instruments")
    @classmethod
    def instruments_not_empty(
        cls, v: dict[str, InstrumentArrangementSpec]
    ) -> dict[str, InstrumentArrangementSpec]:
        """At least one instrument is required."""
        if not v:
            raise SpecValidationError(
                "At least one instrument is required in arrangement",
                field="arrangement.instruments",
            )
        return v


class ProductionSpecV2(BaseModel):
    """Production parameters — v2 adds use_case.

    Attributes:
        use_case: Target use case for perception-layer evaluation.
        target_lufs: Target integrated loudness in LUFS.
        stereo_width: Stereo width (0.0–1.0).
        vocal_space_reserved: Whether to reserve space for vocals.
    """

    use_case: Literal[
        "youtube_bgm", "game_bgm", "advertisement", "study_focus", "general"
    ] = "general"
    target_lufs: float = -14.0
    stereo_width: float = 0.8
    vocal_space_reserved: bool = False

    @field_validator("target_lufs")
    @classmethod
    def lufs_reasonable(cls, v: float) -> float:
        """LUFS must be between -30 and 0."""
        if not -30.0 <= v <= 0.0:
            raise SpecValidationError(
                f"LUFS target must be between -30 and 0, got {v}",
                field="production.target_lufs",
            )
        return v

    @field_validator("stereo_width")
    @classmethod
    def width_in_range(cls, v: float) -> float:
        """Stereo width must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"stereo_width must be 0.0–1.0, got {v}",
                field="production.stereo_width",
            )
        return v


class ConstraintSpecV2(BaseModel):
    """A single constraint in v2 format.

    Attributes:
        kind: Constraint type.
        rule: Rule expression string.
        scope: Scope string (global, section:name, instrument:name, etc.).
        severity: How serious a violation is.
    """

    kind: Literal["must", "must_not", "prefer", "avoid"]
    rule: str
    scope: str = "global"
    severity: Literal["error", "warning", "hint"] = "warning"

    @field_validator("rule")
    @classmethod
    def rule_not_empty(cls, v: str) -> str:
        """Rule must be non-empty."""
        if not v.strip():
            raise SpecValidationError("Constraint rule cannot be empty", field="constraints.rule")
        return v.strip()


class GenerationSpecV2(BaseModel):
    """Generation configuration — v2.

    Currently keeps v1 compatibility with a single `strategy` field.
    Future: plan_strategy and realize_strategy will split this.

    Attributes:
        strategy: Generator strategy name.
        seed: Random seed for reproducibility.
        temperature: Variation control (0.0–1.0).
    """

    strategy: Literal["rule_based", "stochastic"] = "rule_based"
    seed: int | None = None
    temperature: float = 0.5

    @field_validator("temperature")
    @classmethod
    def temperature_in_range(cls, v: float) -> float:
        """Temperature must be in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise SpecValidationError(
                f"Temperature must be 0.0–1.0, got {v}",
                field="generation.temperature",
            )
        return v


# ---------------------------------------------------------------------------
# Top-level v2 spec
# ---------------------------------------------------------------------------


class CompositionSpecV2(BaseModel):
    """Top-level composition specification — v2 schema.

    Structured into 11 named sections for fine-grained musical control.
    The ``version`` field must be ``"2"`` to distinguish from v1.
    """

    version: Literal["2"]
    identity: IdentitySpec
    global_: GlobalSpec = Field(alias="global")
    emotion: EmotionSpec = Field(default_factory=EmotionSpec)
    form: FormSpec
    melody: MelodySpec = Field(default_factory=MelodySpec)
    harmony: HarmonySpec = Field(default_factory=HarmonySpec)
    rhythm: RhythmSpec = Field(default_factory=RhythmSpec)
    drums: DrumsSpec = Field(default_factory=DrumsSpec)
    arrangement: ArrangementSpecV2
    production: ProductionSpecV2 = Field(default_factory=ProductionSpecV2)
    constraints: list[ConstraintSpecV2] = Field(default_factory=list)
    generation: GenerationSpecV2 = Field(default_factory=GenerationSpecV2)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def bars_duration_sanity(self) -> CompositionSpecV2:
        """Warn-level check: total bars should roughly match duration_sec."""
        total_bars = sum(s.bars for s in self.form.sections)
        bpm = self.global_.bpm
        # Parse time signature numerator for beats per bar
        ts_parts = self.global_.time_signature.split("/")
        beats_per_bar = int(ts_parts[0]) if len(ts_parts) == 2 else 4  # noqa: PLR2004
        estimated_secs = (total_bars * beats_per_bar * 60.0) / bpm
        target = self.identity.duration_sec
        # Allow 50% tolerance — this is a sanity check, not a hard constraint
        if target > 0 and abs(estimated_secs - target) / target > 0.5:
            raise SpecValidationError(
                f"Total bars ({total_bars}) at {bpm} BPM ≈ {estimated_secs:.0f}s, "
                f"but identity.duration_sec = {target}s (>50% deviation)",
                field="form / identity.duration_sec",
            )
        return self

    def computed_total_bars(self) -> int:
        """Return total bars from form sections."""
        return sum(s.bars for s in self.form.sections)

    @classmethod
    def from_yaml(cls, path: Path) -> CompositionSpecV2:
        """Load and validate a v2 composition spec from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Validated CompositionSpecV2.

        Raises:
            SpecValidationError: If the YAML is invalid or fails validation.
        """
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            raise SpecValidationError(f"Failed to load YAML: {e}") from e
        if not isinstance(data, dict):
            raise SpecValidationError("YAML root must be a mapping")
        if data.get("version") != "2":
            raise SpecValidationError(
                f"Expected version '2', got '{data.get('version')}'. "
                "Use CompositionSpec (v1) for unversioned specs.",
                field="version",
            )
        try:
            return cls.model_validate(data)
        except SpecValidationError:
            raise
        except Exception as e:
            raise SpecValidationError(f"V2 spec validation failed: {e}") from e

    def to_yaml(self, path: Path) -> None:
        """Dump the spec to a YAML file.

        Args:
            path: Output file path.
        """
        data = self.model_dump(by_alias=True, exclude_none=True)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def to_v1(self) -> Any:
        """Convert to a v1-compatible CompositionSpec for use with legacy generators.

        Returns:
            A CompositionSpec (v1) with fields mapped from v2.
        """
        from yao.schema.composition import (
            CompositionSpec,
            GenerationConfig,
            InstrumentSpec,
            SectionSpec,
        )

        instruments = [
            InstrumentSpec(name=name, role=inst.role)
            for name, inst in self.arrangement.instruments.items()
        ]
        sections = [
            SectionSpec(
                name=s.id,
                bars=s.bars,
                dynamics=s.dynamics or "mf",
            )
            for s in self.form.sections
        ]
        return CompositionSpec(
            title=self.identity.title,
            genre=self.global_.genre,
            key=self.global_.key,
            tempo_bpm=self.global_.bpm,
            time_signature=self.global_.time_signature,
            instruments=instruments,
            sections=sections,
            generation=GenerationConfig(
                strategy=self.generation.strategy,
                seed=self.generation.seed,
                temperature=self.generation.temperature,
            ),
        )
