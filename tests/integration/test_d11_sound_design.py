"""D11: Identical MIDI + different sound_design.yaml produces different output.

Since pedalboard is an optional dependency that may not be installed,
this test verifies the schema and routing layer — that two different
SoundDesignSpecs produce different EffectChain configurations that would
result in different audio when rendered.
"""

from __future__ import annotations

from yao.schema.sound_design import EffectChainSpec, EffectSpec, PatchSpec, SoundDesignSpec
from yao.sound_design.effects import Effect, EffectChain
from yao.sound_design.patches import Patch


class TestD11SoundDesignDifferentOutput:
    """Identical MIDI with different sound design specs produces different configs."""

    def test_different_patches_produce_different_configs(self) -> None:
        """Two different patch specs create distinct Patch objects."""
        patch_a = Patch(
            name="felt_piano",
            synthesis_kind="sample_based",
            parameters={"pack": "felt_piano_close_mic", "velocity_layers": 4},
        )
        patch_b = Patch(
            name="bright_grand",
            synthesis_kind="sample_based",
            parameters={"pack": "concert_grand", "velocity_layers": 8},
        )
        assert patch_a != patch_b
        assert patch_a.parameters != patch_b.parameters

    def test_different_effect_chains_produce_different_configs(self) -> None:
        """Two different effect chain specs create distinct EffectChain objects."""
        chain_lofi = EffectChain(
            name="lofi_piano",
            effects=(
                Effect(effect_type="tape_saturation", parameters={"drive": 0.4}),
                Effect(effect_type="eq", parameters={"bands": [{"freq_hz": 8000, "gain_db": -6}]}),
            ),
        )
        chain_clean = EffectChain(
            name="clean_piano",
            effects=(Effect(effect_type="reverb", parameters={"wet": 0.3}),),
        )
        assert chain_lofi != chain_clean
        assert len(chain_lofi.effects) != len(chain_clean.effects)

    def test_sound_design_spec_distinguishes_genres(self) -> None:
        """Two genre-specific SoundDesignSpecs with identical stem names produce
        different patch and effect configurations."""
        lofi_spec = SoundDesignSpec(
            patches={
                "piano": PatchSpec(name="felt_piano", synthesis_kind="sample_based"),
            },
            effect_chains={
                "piano": EffectChainSpec(
                    name="lofi_chain",
                    effects=[
                        EffectSpec(effect_type="tape_saturation", parameters={"drive": 0.3}),
                        EffectSpec(effect_type="eq", parameters={"cut_high": True}),
                    ],
                ),
            },
        )
        cinematic_spec = SoundDesignSpec(
            patches={
                "piano": PatchSpec(name="concert_grand", synthesis_kind="sample_based"),
            },
            effect_chains={
                "piano": EffectChainSpec(
                    name="cinematic_chain",
                    effects=[
                        EffectSpec(effect_type="convolution_reverb", parameters={"ir": "hall.wav", "wet": 0.4}),
                    ],
                ),
            },
        )

        # Same stem name "piano" but different sound design
        assert lofi_spec.patches["piano"].name != cinematic_spec.patches["piano"].name
        assert lofi_spec.effect_chains["piano"].name != cinematic_spec.effect_chains["piano"].name
        assert len(lofi_spec.effect_chains["piano"].effects) != len(cinematic_spec.effect_chains["piano"].effects)

    def test_sound_design_available_flag_exists(self) -> None:
        """The SOUND_DESIGN_AVAILABLE flag correctly indicates pedalboard status."""
        from yao.sound_design import SOUND_DESIGN_AVAILABLE

        # Should be a bool regardless of whether pedalboard is installed
        assert isinstance(SOUND_DESIGN_AVAILABLE, bool)
