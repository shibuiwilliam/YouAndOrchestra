"""Tests for the Sound Design layer (Layer 3.5).

Tests cover:
- Patch creation and validation
- EffectChain creation and properties
- SoundDesignSpec loading from dict
- Lazy pedalboard import (missing pedalboard doesn't crash)
- Architecture lint passes with the new layer
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from yao.errors import SpecValidationError
from yao.schema.sound_design import (
    SoundDesignSpec,
)
from yao.sound_design.effects import Effect, EffectChain
from yao.sound_design.patches import Patch


class TestPatch:
    """Tests for Patch dataclass creation and validation."""

    def test_create_sample_based_patch(self) -> None:
        """A valid sample_based patch should be created successfully."""
        p = Patch(
            name="warm_piano",
            synthesis_kind="sample_based",
            parameters={"soundfont": "piano.sf2", "preset": 0},
        )
        assert p.name == "warm_piano"
        assert p.synthesis_kind == "sample_based"
        assert p.parameters == {"soundfont": "piano.sf2", "preset": 0}

    def test_create_subtractive_patch(self) -> None:
        """A valid subtractive patch should be created successfully."""
        p = Patch(
            name="bass_synth",
            synthesis_kind="subtractive",
            parameters={"oscillator": "saw", "cutoff_hz": 800},
        )
        assert p.name == "bass_synth"
        assert p.synthesis_kind == "subtractive"

    def test_create_fm_patch(self) -> None:
        """A valid FM patch should be created successfully."""
        p = Patch(
            name="bell",
            synthesis_kind="fm",
            parameters={"carrier_ratio": 1.0, "modulator_ratio": 2.0},
        )
        assert p.synthesis_kind == "fm"

    def test_create_wavetable_patch(self) -> None:
        """A valid wavetable patch should be created successfully."""
        p = Patch(
            name="pad",
            synthesis_kind="wavetable",
            parameters={"table": "basic_shapes", "position": 0.5},
        )
        assert p.synthesis_kind == "wavetable"

    def test_create_physical_patch(self) -> None:
        """A valid physical modeling patch should be created successfully."""
        p = Patch(
            name="pluck",
            synthesis_kind="physical",
            parameters={"model": "karplus_strong", "damping": 0.5},
        )
        assert p.synthesis_kind == "physical"

    def test_empty_name_raises(self) -> None:
        """An empty patch name should raise SpecValidationError."""
        with pytest.raises(SpecValidationError, match="name must not be empty"):
            Patch(name="", synthesis_kind="fm")

    def test_default_parameters_empty_dict(self) -> None:
        """Parameters should default to an empty dict."""
        p = Patch(name="minimal", synthesis_kind="subtractive")
        assert p.parameters == {}

    def test_patch_is_frozen(self) -> None:
        """Patches should be immutable (frozen dataclass)."""
        p = Patch(name="test", synthesis_kind="fm")
        with pytest.raises(AttributeError):
            p.name = "changed"  # type: ignore[misc]


class TestEffect:
    """Tests for Effect dataclass."""

    def test_create_reverb_effect(self) -> None:
        """A reverb effect should be created with parameters."""
        e = Effect(
            effect_type="reverb",
            parameters={"room_size": 0.7, "damping": 0.5, "wet": 0.3},
        )
        assert e.effect_type == "reverb"
        assert e.parameters["room_size"] == 0.7
        assert e.bypass is False

    def test_create_bypassed_effect(self) -> None:
        """A bypassed effect should preserve its configuration."""
        e = Effect(effect_type="compressor", bypass=True)
        assert e.bypass is True

    def test_invalid_effect_type_raises(self) -> None:
        """An invalid effect type should raise SpecValidationError."""
        with pytest.raises(SpecValidationError, match="Invalid effect type"):
            Effect(effect_type="wah_wah")  # type: ignore[arg-type]

    def test_effect_is_frozen(self) -> None:
        """Effects should be immutable."""
        e = Effect(effect_type="eq")
        with pytest.raises(AttributeError):
            e.bypass = True  # type: ignore[misc]


class TestEffectChain:
    """Tests for EffectChain dataclass."""

    def test_create_chain_with_effects(self) -> None:
        """An effect chain should hold an ordered tuple of effects."""
        e1 = Effect(effect_type="eq", parameters={"frequency_hz": 200})
        e2 = Effect(effect_type="reverb", parameters={"room_size": 0.6})
        chain = EffectChain(name="piano_chain", effects=(e1, e2))
        assert chain.name == "piano_chain"
        assert len(chain.effects) == 2
        assert chain.effects[0].effect_type == "eq"
        assert chain.effects[1].effect_type == "reverb"

    def test_active_effects_excludes_bypassed(self) -> None:
        """active_effects should filter out bypassed effects."""
        e1 = Effect(effect_type="eq", bypass=False)
        e2 = Effect(effect_type="compressor", bypass=True)
        e3 = Effect(effect_type="reverb", bypass=False)
        chain = EffectChain(name="test", effects=(e1, e2, e3))
        active = chain.active_effects
        assert len(active) == 2
        assert all(not e.bypass for e in active)

    def test_is_empty_when_all_bypassed(self) -> None:
        """is_empty should return True when all effects are bypassed."""
        e1 = Effect(effect_type="eq", bypass=True)
        chain = EffectChain(name="silent", effects=(e1,))
        assert chain.is_empty is True

    def test_is_empty_when_no_effects(self) -> None:
        """is_empty should return True for an empty chain."""
        chain = EffectChain(name="empty")
        assert chain.is_empty is True

    def test_empty_name_raises(self) -> None:
        """An empty chain name should raise SpecValidationError."""
        with pytest.raises(SpecValidationError, match="name must not be empty"):
            EffectChain(name="")

    def test_chain_is_frozen(self) -> None:
        """EffectChain should be immutable."""
        chain = EffectChain(name="test")
        with pytest.raises(AttributeError):
            chain.name = "changed"  # type: ignore[misc]


class TestSoundDesignSpec:
    """Tests for SoundDesignSpec Pydantic model."""

    def test_load_from_dict(self) -> None:
        """SoundDesignSpec should load from a dictionary (simulating YAML)."""
        data = {
            "patches": {
                "piano": {
                    "name": "warm_piano",
                    "synthesis_kind": "sample_based",
                    "parameters": {"soundfont": "piano.sf2", "preset": 0},
                },
                "bass": {
                    "name": "sub_bass",
                    "synthesis_kind": "subtractive",
                    "parameters": {"oscillator": "sine", "cutoff_hz": 200},
                },
            },
            "effect_chains": {
                "piano": {
                    "name": "piano_chain",
                    "effects": [
                        {
                            "effect_type": "eq",
                            "parameters": {"frequency_hz": 200, "gain_db": -2},
                        },
                        {
                            "effect_type": "reverb",
                            "parameters": {"room_size": 0.6, "wet": 0.25},
                        },
                    ],
                },
            },
        }
        spec = SoundDesignSpec.model_validate(data)
        assert "piano" in spec.patches
        assert spec.patches["piano"].synthesis_kind == "sample_based"
        assert "piano" in spec.effect_chains
        assert len(spec.effect_chains["piano"].effects) == 2

    def test_empty_spec_is_valid(self) -> None:
        """An empty SoundDesignSpec is valid (sound design is optional)."""
        spec = SoundDesignSpec.model_validate({})
        assert spec.patches == {}
        assert spec.effect_chains == {}

    def test_invalid_synthesis_kind_rejected(self) -> None:
        """An invalid synthesis kind should fail validation."""
        data = {
            "patches": {
                "piano": {
                    "name": "test",
                    "synthesis_kind": "granular",  # not supported
                }
            }
        }
        with pytest.raises((ValueError, TypeError)):
            SoundDesignSpec.model_validate(data)

    def test_invalid_effect_type_rejected(self) -> None:
        """An invalid effect type should fail validation."""
        data = {
            "effect_chains": {
                "piano": {
                    "name": "test_chain",
                    "effects": [{"effect_type": "wah_wah"}],
                }
            }
        }
        with pytest.raises((ValueError, TypeError)):
            SoundDesignSpec.model_validate(data)


class TestLazyPedalboardImport:
    """Tests for lazy pedalboard import behavior."""

    def test_sound_design_module_imports_without_pedalboard(self) -> None:
        """The sound_design module should import even without pedalboard."""
        # This test inherently passes if we got this far — the module
        # was imported at the top of this test file. But let's be explicit.
        from yao.sound_design import SOUND_DESIGN_AVAILABLE

        # SOUND_DESIGN_AVAILABLE may be True or False depending on env;
        # the key assertion is that importing didn't crash.
        assert isinstance(SOUND_DESIGN_AVAILABLE, bool)

    def test_pedalboard_not_at_module_level_in_patches(self) -> None:
        """patches.py must not import pedalboard at module level."""
        import ast
        from pathlib import Path

        patches_path = Path("src/yao/sound_design/patches.py")
        source = patches_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pedalboard"), (
                        "patches.py must not import pedalboard at module level"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("pedalboard"), "patches.py must not import pedalboard at module level"

    def test_pedalboard_not_at_module_level_in_effects(self) -> None:
        """effects.py must not import pedalboard at module level."""
        import ast
        from pathlib import Path

        effects_path = Path("src/yao/sound_design/effects.py")
        source = effects_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("pedalboard"), (
                        "effects.py must not import pedalboard at module level"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("pedalboard"), "effects.py must not import pedalboard at module level"


class TestArchitectureLint:
    """Test that architecture lint passes with the new sound_design layer."""

    def test_architecture_lint_passes(self) -> None:
        """The architecture lint tool should pass with sound_design at layer 3."""
        result = subprocess.run(
            [sys.executable, "tools/architecture_lint.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Architecture lint failed:\n{result.stdout}\n{result.stderr}"
