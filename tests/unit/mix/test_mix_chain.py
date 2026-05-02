"""Integration tests for the full mix chain."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

pedalboard = pytest.importorskip("pedalboard")

from yao.mix.mix_chain import MixChainProcessor  # noqa: E402
from yao.schema.production import (  # noqa: E402
    CompressionSpec,
    EQBand,
    MasterSpec,
    ProductionManifest,
    ReverbSpec,
    TrackMixSpec,
)


@pytest.fixture()
def stems_dir(tmp_path: Path) -> Path:
    """Create a stems directory with two instrument WAV files."""
    stems = tmp_path / "stems"
    stems.mkdir()

    sr = 44100
    duration = 2.0
    samples = int(sr * duration)
    t = np.linspace(0.0, duration, samples, endpoint=False)

    # Piano stem: 440Hz sine
    piano = (0.4 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    sf.write(str(stems / "piano.wav"), piano, sr)

    # Bass stem: 110Hz sine
    bass = (0.5 * np.sin(2 * np.pi * 110 * t)).astype(np.float32)
    sf.write(str(stems / "bass.wav"), bass, sr)

    return stems


class TestMixChainIntegration:
    def test_basic_mix(self, stems_dir: Path, tmp_path: Path) -> None:
        manifest = ProductionManifest(
            master=MasterSpec(target_lufs=-14.0),
        )
        output = tmp_path / "mixed.wav"

        processor = MixChainProcessor()
        result_path = processor.process(stems_dir, manifest, output)

        assert result_path.exists()
        audio, sr = sf.read(str(result_path))
        assert sr == 44100
        assert audio.ndim == 2  # stereo
        assert len(audio) > 0

    def test_with_per_track_effects(self, stems_dir: Path, tmp_path: Path) -> None:
        manifest = ProductionManifest(
            master=MasterSpec(target_lufs=-14.0),
            per_track={
                "piano": TrackMixSpec(
                    eq=[EQBand(freq=200.0, type="high_pass")],
                    reverb=ReverbSpec(type="room", wet=0.2),
                    pan=-0.3,
                    gain_db=-2.0,
                ),
                "bass": TrackMixSpec(
                    compression=CompressionSpec(threshold_db=-12.0, ratio=3.0),
                    pan=0.0,
                ),
            },
        )
        output = tmp_path / "mixed_fx.wav"

        processor = MixChainProcessor()
        result_path = processor.process(stems_dir, manifest, output)

        assert result_path.exists()
        audio, _ = sf.read(str(result_path))
        assert audio.ndim == 2

    def test_empty_stems_raises(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty_stems"
        empty_dir.mkdir()

        manifest = ProductionManifest()
        processor = MixChainProcessor()

        from yao.errors import RenderError

        with pytest.raises(RenderError, match="No WAV stems"):
            processor.process(empty_dir, manifest, tmp_path / "out.wav")

    def test_output_is_stereo(self, stems_dir: Path, tmp_path: Path) -> None:
        manifest = ProductionManifest()
        output = tmp_path / "stereo.wav"

        processor = MixChainProcessor()
        processor.process(stems_dir, manifest, output)

        audio, _ = sf.read(str(output))
        assert audio.ndim == 2
        assert audio.shape[1] == 2
