"""Mix chain processor — applies per-track and master effects.

Reads rendered WAV stems, applies per-track EQ/compression/reverb/gain/pan,
mixes down to stereo, and applies the master chain.

Belongs to Layer 5 (Mix Chain).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import soundfile as sf
import structlog

from yao.errors import RenderError
from yao.mix.compression import apply_compression
from yao.mix.eq import apply_eq
from yao.mix.master_chain import apply_master
from yao.mix.reverb import apply_reverb
from yao.schema.production import ProductionManifest, TrackMixSpec

_NDFloat = npt.NDArray[np.floating[Any]]

logger = structlog.get_logger()


class MixChainProcessor:
    """Applies a ProductionManifest to rendered audio stems.

    Usage::

        processor = MixChainProcessor()
        processor.process(
            stems_dir=Path("outputs/.../stems/"),
            manifest=manifest,
            output_path=Path("outputs/.../mixed.wav"),
        )
    """

    def process(
        self,
        stems_dir: Path,
        manifest: ProductionManifest,
        output_path: Path,
        sr: int = 44100,
    ) -> Path:
        """Process stems through the mix chain and write output.

        Args:
            stems_dir: Directory containing per-instrument WAV stems.
            manifest: Production manifest with per-track and master specs.
            output_path: Path for the mixed output WAV.
            sr: Expected sample rate.

        Returns:
            Path to the written output file.

        Raises:
            RenderError: If no stems found or processing fails.
        """
        stem_files = sorted(stems_dir.glob("*.wav"))
        if not stem_files:
            raise RenderError(f"No WAV stems found in {stems_dir}")

        # Load and process each stem
        max_length = 0

        processed_stems: list[tuple[str, _NDFloat]] = []
        for stem_path in stem_files:
            instrument = stem_path.stem
            audio, file_sr = sf.read(str(stem_path), dtype="float32")
            if file_sr != sr:
                logger.warning(
                    "sample_rate_mismatch",
                    stem=instrument,
                    expected=sr,
                    got=file_sr,
                )

            # Ensure mono → shape (samples,)
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)

            track_spec = manifest.per_track.get(instrument, TrackMixSpec())
            audio = self._apply_track_chain(audio, sr, track_spec)

            max_length = max(max_length, len(audio))
            processed_stems.append((instrument, audio))

        # Mix down to stereo
        left = np.zeros(max_length, dtype=np.float32)
        right = np.zeros(max_length, dtype=np.float32)

        for instrument, audio in processed_stems:
            track_spec = manifest.per_track.get(instrument, TrackMixSpec())
            pan = track_spec.pan  # -1.0 = left, 0.0 = center, 1.0 = right

            # Constant-power pan law
            left_gain = float(np.cos((pan + 1.0) * np.pi / 4.0))
            right_gain = float(np.sin((pan + 1.0) * np.pi / 4.0))

            n = len(audio)
            left[:n] += audio * left_gain
            right[:n] += audio * right_gain

        stereo = np.column_stack([left, right])

        # Master chain
        mastered = apply_master(stereo, sr, manifest.master)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), mastered, sr)

        logger.info(
            "mix_chain_complete",
            stems=len(processed_stems),
            output=str(output_path),
        )

        return output_path

    def _apply_track_chain(
        self,
        audio: _NDFloat,
        sr: int,
        spec: TrackMixSpec,
    ) -> _NDFloat:
        """Apply per-track effects chain.

        Order: gain → EQ → compression → reverb.
        """
        result = audio.copy()

        # Gain
        if spec.gain_db != 0.0:
            gain_linear = 10.0 ** (spec.gain_db / 20.0)
            result = (result * gain_linear).astype(result.dtype)

        # EQ
        if spec.eq:
            result = apply_eq(result, sr, spec.eq)

        # Compression
        if spec.compression is not None:
            result = apply_compression(result, sr, spec.compression)

        # Reverb
        if spec.reverb is not None:
            result = apply_reverb(result, sr, spec.reverb)

        return result
