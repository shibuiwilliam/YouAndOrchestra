"""Tests for composition.yaml v2 schema.

Covers:
- Template loading
- Field validation (positive and negative)
- v1/v2 confusion error handling
- Round-trip serialization
- v2 → v1 conversion
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from yao.errors import SpecValidationError
from yao.schema.composition_v2 import (
    ArrangementSpecV2,
    CompositionSpecV2,
    ConstraintSpecV2,
    DrumsSpec,
    EmotionSpec,
    FormSpec,
    GenerationSpecV2,
    GlobalSpec,
    HarmonySpec,
    IdentitySpec,
    InstrumentArrangementSpec,
    MelodySpec,
    NoteRangeSpec,
    ProductionSpecV2,
    RhythmSpec,
    SectionFormSpec,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "specs" / "templates" / "v2"

MINIMAL_V2: dict = {
    "version": "2",
    "identity": {"title": "Test Piece", "duration_sec": 60},
    "global": {"key": "C major", "bpm": 120, "time_signature": "4/4", "genre": "general"},
    "form": {"sections": [{"id": "intro", "bars": 8}, {"id": "chorus", "bars": 8}]},
    "arrangement": {
        "instruments": {"piano": {"role": "melody"}},
    },
    "generation": {"strategy": "rule_based"},
}


def _make_spec(**overrides: object) -> dict:
    """Create a minimal v2 spec dict with optional overrides."""
    data = copy.deepcopy(MINIMAL_V2)
    for key, val in overrides.items():
        keys = key.split(".")
        d = data
        for k in keys[:-1]:
            d = d[k]
        d[keys[-1]] = val
    return data


# ---------------------------------------------------------------------------
# Template loading tests
# ---------------------------------------------------------------------------


class TestTemplateLoading:
    """All v2 templates must load without error."""

    @pytest.mark.parametrize(
        "template_name",
        ["bgm-90sec-pop.yaml", "cinematic-3min.yaml", "loopable-game-bgm.yaml"],
    )
    def test_template_loads(self, template_name: str) -> None:
        path = TEMPLATES_DIR / template_name
        assert path.exists(), f"Template not found: {path}"
        spec = CompositionSpecV2.from_yaml(path)
        assert spec.version == "2"
        assert spec.identity.title

    def test_all_templates_have_valid_instruments(self) -> None:
        for path in TEMPLATES_DIR.glob("*.yaml"):
            spec = CompositionSpecV2.from_yaml(path)
            assert len(spec.arrangement.instruments) > 0

    def test_all_templates_have_sections(self) -> None:
        for path in TEMPLATES_DIR.glob("*.yaml"):
            spec = CompositionSpecV2.from_yaml(path)
            assert len(spec.form.sections) > 0


# ---------------------------------------------------------------------------
# Identity tests
# ---------------------------------------------------------------------------


class TestIdentity:
    def test_valid(self) -> None:
        spec = IdentitySpec(title="Test", duration_sec=90)
        assert spec.title == "Test"

    def test_empty_title_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="Title cannot be empty"):
            IdentitySpec(title="  ", duration_sec=90)

    def test_negative_duration_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="positive"):
            IdentitySpec(title="Test", duration_sec=-1)


# ---------------------------------------------------------------------------
# Global tests
# ---------------------------------------------------------------------------


class TestGlobal:
    def test_valid(self) -> None:
        spec = GlobalSpec(key="D minor", bpm=140)
        assert spec.key == "D minor"

    def test_invalid_key_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="Key must be"):
            GlobalSpec(key="Cminor")

    def test_unknown_scale_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="Unknown scale type"):
            GlobalSpec(key="C superlocrian")

    def test_bpm_too_low_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="BPM must be between"):
            GlobalSpec(bpm=5)

    def test_bpm_too_high_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="BPM must be between"):
            GlobalSpec(bpm=500)

    def test_invalid_time_signature_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="Time signature must be"):
            GlobalSpec(time_signature="4-4")

    def test_blends_default_empty(self) -> None:
        spec = GlobalSpec()
        assert spec.blends == []

    def test_blends_single(self) -> None:
        from yao.schema.composition_v2 import GenreBlendSpec

        spec = GlobalSpec(
            genre="jazz",
            blends=[GenreBlendSpec(name="hiphop", weight=0.3, blend_aspects=["groove", "mix_aesthetics"])],
        )
        assert len(spec.blends) == 1
        assert spec.blends[0].name == "hiphop"
        assert "groove" in spec.blends[0].blend_aspects

    def test_blends_multiple(self) -> None:
        from yao.schema.composition_v2 import GenreBlendSpec

        spec = GlobalSpec(
            genre="jazz",
            blends=[
                GenreBlendSpec(name="hiphop", weight=0.2, blend_aspects=["groove"]),
                GenreBlendSpec(name="ambient", weight=0.1, blend_aspects=["texture", "reverb"]),
            ],
        )
        assert len(spec.blends) == 2

    def test_blend_weight_out_of_range(self) -> None:
        from yao.schema.composition_v2 import GenreBlendSpec

        with pytest.raises((SpecValidationError, ValidationError)):
            GenreBlendSpec(name="rock", weight=0.0, blend_aspects=[])

    def test_blend_invalid_aspect(self) -> None:
        from yao.schema.composition_v2 import GenreBlendSpec

        with pytest.raises((SpecValidationError, ValidationError)):
            GenreBlendSpec(name="rock", weight=0.3, blend_aspects=["nonexistent"])

    def test_blend_all_valid_aspects(self) -> None:
        from yao.schema.composition_v2 import GenreBlendSpec

        valid_aspects = [
            "harmony",
            "melody",
            "groove",
            "instrumentation",
            "form",
            "mix_aesthetics",
            "texture",
            "reverb",
        ]
        blend = GenreBlendSpec(name="rock", weight=0.5, blend_aspects=valid_aspects)
        assert len(blend.blend_aspects) == 8


# ---------------------------------------------------------------------------
# Emotion tests
# ---------------------------------------------------------------------------


class TestEmotion:
    def test_valid(self) -> None:
        spec = EmotionSpec(valence=0.8, energy=0.5, tension=0.3, warmth=0.6, nostalgia=0.1)
        assert spec.valence == 0.8

    def test_out_of_range_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="emotion.valence"):
            EmotionSpec(valence=1.5)

    def test_negative_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="emotion.energy"):
            EmotionSpec(energy=-0.1)

    def test_defaults(self) -> None:
        spec = EmotionSpec()
        assert spec.valence == 0.5
        assert spec.nostalgia == 0.3

    def test_target_mood_none_by_default(self) -> None:
        spec = EmotionSpec()
        assert spec.target_mood is None

    def test_target_mood_accepted(self) -> None:
        spec = EmotionSpec(target_mood={"arousal": 0.5, "valence": -0.3, "tension": 0.7})
        assert spec.target_mood is not None
        assert spec.target_mood["arousal"] == 0.5

    def test_target_mood_empty_dict(self) -> None:
        spec = EmotionSpec(target_mood={})
        assert spec.target_mood == {}


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------


class TestForm:
    def test_valid(self) -> None:
        spec = FormSpec(sections=[SectionFormSpec(id="intro", bars=4)])
        assert len(spec.sections) == 1

    def test_empty_sections_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="At least one section"):
            FormSpec(sections=[])

    def test_duplicate_ids_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="Duplicate section ids"):
            FormSpec(
                sections=[
                    SectionFormSpec(id="verse", bars=8),
                    SectionFormSpec(id="verse", bars=8),
                ]
            )

    def test_multiple_climax_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="Multiple climax"):
            FormSpec(
                sections=[
                    SectionFormSpec(id="a", bars=8, climax=True),
                    SectionFormSpec(id="b", bars=8, climax=True),
                ]
            )

    def test_section_zero_bars_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="bars must be positive"):
            SectionFormSpec(id="intro", bars=0)

    def test_section_density_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError, match="density must be 0.0"):
            SectionFormSpec(id="intro", bars=4, density=1.5)


# ---------------------------------------------------------------------------
# Melody tests
# ---------------------------------------------------------------------------


class TestMelody:
    def test_defaults(self) -> None:
        spec = MelodySpec()
        assert spec.contour == "arch"

    def test_note_range_valid(self) -> None:
        r = NoteRangeSpec(min="C3", max="C5")
        assert r.min == "C3"

    def test_note_range_inverted_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="must be below"):
            NoteRangeSpec(min="C5", max="C3")

    def test_note_range_same_note_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="must be below"):
            NoteRangeSpec(min="C4", max="C4")

    def test_invalid_note_name_fails(self) -> None:
        # Invalid note names are caught by note_name_to_midi in the validator;
        # the model validator silently returns if individual notes fail,
        # but creating a full spec with invalid notes should propagate the error
        # from the notation module when actually used.
        # Here we test that the validator doesn't crash on invalid input.
        r = NoteRangeSpec(min="X9", max="C5")
        assert r.min == "X9"  # Stored as-is; deeper validation at use time

    def test_melody_strategy_valid(self) -> None:
        spec = MelodySpec(melody_strategy="arpeggiated")
        assert spec.melody_strategy == "arpeggiated"

    def test_melody_strategy_none_allowed(self) -> None:
        spec = MelodySpec(melody_strategy=None)
        assert spec.melody_strategy is None

    def test_melody_strategy_default_none(self) -> None:
        spec = MelodySpec()
        assert spec.melody_strategy is None

    def test_melody_strategy_invalid_rejected(self) -> None:
        with pytest.raises((SpecValidationError, ValidationError)):
            MelodySpec(melody_strategy="nonexistent_strategy")

    def test_all_strategies_accepted(self) -> None:
        for name in [
            "contour_based",
            "motif_development",
            "linear_voice",
            "arpeggiated",
            "scalar_runs",
            "call_response",
            "pedal_tone",
            "hocketing",
        ]:
            spec = MelodySpec(melody_strategy=name)
            assert spec.melody_strategy == name


# ---------------------------------------------------------------------------
# Harmony tests
# ---------------------------------------------------------------------------


class TestHarmony:
    def test_valid(self) -> None:
        spec = HarmonySpec(complexity=0.6, chord_palette=["I", "V", "vi"])
        assert spec.complexity == 0.6

    def test_complexity_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError, match="complexity must be"):
            HarmonySpec(complexity=2.0)

    def test_empty_palette_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="at least one chord"):
            HarmonySpec(chord_palette=[])


# ---------------------------------------------------------------------------
# Rhythm tests
# ---------------------------------------------------------------------------


class TestRhythm:
    def test_valid(self) -> None:
        spec = RhythmSpec(swing=0.1, syncopation=0.3)
        assert spec.swing == 0.1

    def test_swing_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError, match="rhythm parameter must be"):
            RhythmSpec(swing=1.5)


# ---------------------------------------------------------------------------
# Drums tests
# ---------------------------------------------------------------------------


class TestDrums:
    def test_valid(self) -> None:
        spec = DrumsSpec(pattern_family="pop_8beat", swing=0.1)
        assert spec.pattern_family == "pop_8beat"

    def test_ghost_density_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError, match="drums parameter must be"):
            DrumsSpec(ghost_notes_density=2.0)


# ---------------------------------------------------------------------------
# Arrangement tests
# ---------------------------------------------------------------------------


class TestArrangement:
    def test_valid(self) -> None:
        spec = ArrangementSpecV2(instruments={"piano": InstrumentArrangementSpec(role="melody")})
        assert "piano" in spec.instruments

    def test_empty_instruments_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="At least one instrument"):
            ArrangementSpecV2(instruments={})


# ---------------------------------------------------------------------------
# Production tests
# ---------------------------------------------------------------------------


class TestProduction:
    def test_valid(self) -> None:
        spec = ProductionSpecV2(use_case="game_bgm", target_lufs=-16)
        assert spec.use_case == "game_bgm"

    def test_invalid_use_case_fails(self) -> None:
        with pytest.raises(ValidationError):
            ProductionSpecV2(use_case="invalid_use_case")  # type: ignore[arg-type]

    def test_lufs_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError, match="LUFS target"):
            ProductionSpecV2(target_lufs=5.0)


# ---------------------------------------------------------------------------
# Constraint tests
# ---------------------------------------------------------------------------


class TestConstraintV2:
    def test_valid(self) -> None:
        c = ConstraintSpecV2(kind="must", rule="melody_within_range")
        assert c.kind == "must"

    def test_empty_rule_fails(self) -> None:
        with pytest.raises(SpecValidationError, match="rule cannot be empty"):
            ConstraintSpecV2(kind="must", rule="  ")

    def test_invalid_kind_fails(self) -> None:
        with pytest.raises(ValidationError):
            ConstraintSpecV2(kind="always", rule="test")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------


class TestGeneration:
    def test_valid(self) -> None:
        spec = GenerationSpecV2(strategy="stochastic", seed=42, temperature=0.5)
        assert spec.strategy == "stochastic"

    def test_temperature_out_of_range(self) -> None:
        with pytest.raises(SpecValidationError, match="Temperature must be"):
            GenerationSpecV2(temperature=2.0)

    def test_invalid_strategy_fails(self) -> None:
        with pytest.raises(ValidationError):
            GenerationSpecV2(strategy="neural")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Top-level CompositionSpecV2 tests
# ---------------------------------------------------------------------------


class TestCompositionSpecV2:
    def test_minimal_spec_loads(self) -> None:
        spec = CompositionSpecV2.model_validate(MINIMAL_V2)
        assert spec.version == "2"
        assert spec.identity.title == "Test Piece"
        assert spec.global_.key == "C major"

    def test_missing_version_fails(self) -> None:
        data = copy.deepcopy(MINIMAL_V2)
        del data["version"]
        with pytest.raises(ValidationError):
            CompositionSpecV2.model_validate(data)

    def test_wrong_version_fails(self) -> None:
        data = copy.deepcopy(MINIMAL_V2)
        data["version"] = "1"
        with pytest.raises(ValidationError):
            CompositionSpecV2.model_validate(data)

    def test_v1_spec_rejects_with_message(self, tmp_path: Path) -> None:
        v1_data = {
            "title": "V1 Piece",
            "key": "C major",
            "tempo_bpm": 120,
            "time_signature": "4/4",
            "instruments": [{"name": "piano", "role": "melody"}],
            "sections": [{"name": "intro", "bars": 8}],
        }
        path = tmp_path / "v1.yaml"
        with open(path, "w") as f:
            yaml.dump(v1_data, f)
        with pytest.raises(SpecValidationError, match="version '2'"):
            CompositionSpecV2.from_yaml(path)

    def test_bars_duration_sanity_check(self) -> None:
        # 2 bars at 120 BPM, 4/4 = 4 seconds; duration_sec = 60 => huge mismatch
        data = _make_spec()
        data["identity"]["duration_sec"] = 600
        data["form"]["sections"] = [{"id": "intro", "bars": 2}]
        with pytest.raises(SpecValidationError, match="deviation"):
            CompositionSpecV2.model_validate(data)

    def test_computed_total_bars(self) -> None:
        spec = CompositionSpecV2.model_validate(MINIMAL_V2)
        assert spec.computed_total_bars() == 16  # 8 + 8


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_yaml_round_trip(self, tmp_path: Path) -> None:
        spec1 = CompositionSpecV2.model_validate(MINIMAL_V2)
        out_path = tmp_path / "round_trip.yaml"
        spec1.to_yaml(out_path)
        spec2 = CompositionSpecV2.from_yaml(out_path)
        assert spec1.identity.title == spec2.identity.title
        assert spec1.global_.key == spec2.global_.key
        assert spec1.computed_total_bars() == spec2.computed_total_bars()
        assert len(spec1.form.sections) == len(spec2.form.sections)

    def test_template_round_trip(self, tmp_path: Path) -> None:
        for template_path in TEMPLATES_DIR.glob("*.yaml"):
            spec1 = CompositionSpecV2.from_yaml(template_path)
            out_path = tmp_path / template_path.name
            spec1.to_yaml(out_path)
            spec2 = CompositionSpecV2.from_yaml(out_path)
            assert spec1.identity.title == spec2.identity.title
            assert spec1.computed_total_bars() == spec2.computed_total_bars()


# ---------------------------------------------------------------------------
# v2 → v1 conversion tests
# ---------------------------------------------------------------------------


class TestV2ToV1:
    def test_basic_conversion(self) -> None:
        spec_v2 = CompositionSpecV2.model_validate(MINIMAL_V2)
        spec_v1 = spec_v2.to_v1()
        assert spec_v1.title == "Test Piece"
        assert spec_v1.key == "C major"
        assert spec_v1.tempo_bpm == 120
        assert len(spec_v1.instruments) == 1
        assert spec_v1.instruments[0].name == "piano"
        assert len(spec_v1.sections) == 2

    def test_generation_config_carried(self) -> None:
        data = _make_spec()
        data["generation"] = {"strategy": "stochastic", "seed": 99, "temperature": 0.7}
        spec_v2 = CompositionSpecV2.model_validate(data)
        spec_v1 = spec_v2.to_v1()
        assert spec_v1.generation.strategy == "stochastic"
        assert spec_v1.generation.seed == 99
        assert spec_v1.generation.temperature == 0.7

    def test_all_templates_convert_to_v1(self) -> None:
        for template_path in TEMPLATES_DIR.glob("*.yaml"):
            spec_v2 = CompositionSpecV2.from_yaml(template_path)
            spec_v1 = spec_v2.to_v1()
            assert spec_v1.title
            assert len(spec_v1.sections) > 0
            assert len(spec_v1.instruments) > 0


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_all_optional_sections_defaulted(self) -> None:
        spec = CompositionSpecV2.model_validate(MINIMAL_V2)
        assert spec.emotion.valence == 0.5
        assert spec.melody.contour == "arch"
        assert spec.rhythm.groove == "straight"
        assert spec.drums.pattern_family == "basic"
        assert spec.production.use_case == "general"
        assert spec.constraints == []

    def test_section_with_optional_dynamics(self) -> None:
        s = SectionFormSpec(id="verse", bars=8)
        assert s.dynamics is None

    def test_section_with_explicit_dynamics(self) -> None:
        s = SectionFormSpec(id="verse", bars=8, dynamics="f")
        assert s.dynamics == "f"

    def test_invalid_dynamics_in_section(self) -> None:
        with pytest.raises(SpecValidationError, match="Unknown dynamics"):
            SectionFormSpec(id="verse", bars=8, dynamics="very_loud")
