"""Tests for Stable Audio Open bridge.

All tests use mocks — no GPU or audiocraft required.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from yao.errors import NeuralBackendUnavailableError
from yao.reflect.provenance import ProvenanceLog

# Patch target for skipping the backend check (torch import)
_BACKEND_CHECK = "yao.generators.neural.stable_audio_bridge._check_backend"
# Patch target for the model version (also imports torch)
_MODEL_VERSION = "yao.generators.neural.stable_audio_bridge.StableAudioTextureGenerator._get_model_version"
_MOCK_VERSION = "stable_audio_open_mock"


class TestBackendAvailability:
    def test_import_without_torch_raises(self) -> None:
        """If torch is not importable, generate_texture raises clearly."""
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        with (
            patch.dict("sys.modules", {"torch": None}),
            patch(
                _BACKEND_CHECK,
                side_effect=NeuralBackendUnavailableError("torch not installed"),
            ),
            pytest.raises(NeuralBackendUnavailableError, match="torch"),
        ):
            gen.generate_texture(
                prompt="test",
                output_path=Path("/tmp/test.wav"),
            )


class TestProvenanceFields:
    def test_all_required_fields_present(self, tmp_path: Path) -> None:
        """Provenance must contain model_version, prompt, seed, output_hash, rights_status."""
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        prov = ProvenanceLog()
        output = tmp_path / "texture.wav"

        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            result = gen.generate_texture(
                prompt="warm analog pad",
                output_path=output,
                duration_sec=1.0,
                seed=42,
                provenance=prov,
            )

        # Check result fields
        assert result.model_version == _MOCK_VERSION
        assert result.prompt == "warm analog pad"
        assert result.seed == 42
        assert result.output_hash.startswith("sha256:")
        assert result.rights_status == "model_license_stable_audio_open"

        # Check provenance record
        neural_rec = next(r for r in prov.records if r.operation == "neural_texture_generation")
        params = neural_rec.parameters or {}
        assert "model_version" in params
        assert "prompt" in params
        assert "seed" in params
        assert "output_hash" in params
        assert "rights_status" in params

    def test_output_hash_is_sha256(self, tmp_path: Path) -> None:
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        output = tmp_path / "hash_test.wav"
        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            result = gen.generate_texture(prompt="test", output_path=output, duration_sec=0.5)
        assert result.output_hash.startswith("sha256:")
        assert len(result.output_hash) > 10

    def test_rights_status_default(self, tmp_path: Path) -> None:
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        output = tmp_path / "rights_test.wav"
        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            result = gen.generate_texture(prompt="test", output_path=output, duration_sec=0.5)
        assert result.rights_status == "model_license_stable_audio_open"

    def test_prompt_recorded(self, tmp_path: Path) -> None:
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        prov = ProvenanceLog()
        output = tmp_path / "prompt_test.wav"
        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            gen.generate_texture(
                prompt="lush reverb strings in D minor",
                output_path=output,
                duration_sec=0.5,
                provenance=prov,
            )
        rec = next(r for r in prov.records if r.operation == "neural_texture_generation")
        assert rec.parameters["prompt"] == "lush reverb strings in D minor"

    def test_seed_deterministic(self, tmp_path: Path) -> None:
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        out1 = tmp_path / "det1.wav"
        out2 = tmp_path / "det2.wav"
        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            r1 = gen.generate_texture(prompt="test", output_path=out1, seed=42, duration_sec=0.5)
            r2 = gen.generate_texture(prompt="test", output_path=out2, seed=42, duration_sec=0.5)
        assert r1.output_hash == r2.output_hash


class TestUnknownRights:
    def test_unknown_rights_warns(self, tmp_path: Path) -> None:
        """rights_status='unknown' should trigger a warning."""
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        output = tmp_path / "unknown_rights.wav"

        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            result = gen.generate_texture(
                prompt="test",
                output_path=output,
                duration_sec=0.5,
                rights_status="unknown",
            )
        assert result.rights_status == "unknown"


class TestOutputFile:
    def test_wav_file_created(self, tmp_path: Path) -> None:
        from yao.generators.neural.stable_audio_bridge import StableAudioTextureGenerator

        gen = StableAudioTextureGenerator()
        output = tmp_path / "output.wav"
        with patch(_BACKEND_CHECK), patch(_MODEL_VERSION, return_value=_MOCK_VERSION):
            gen.generate_texture(prompt="test", output_path=output, duration_sec=0.5)
        assert output.exists()
        assert output.stat().st_size > 0
