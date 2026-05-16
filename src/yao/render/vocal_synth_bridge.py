"""Vocal Synthesis Bridge — interface for external vocal engines.

Provides an abstract bridge for sending vocal MIDI + lyrics to external
vocal synthesis engines (VOCALOID, CeVIO, NEUTRINO, etc.) and receiving
rendered audio back.

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import structlog

from yao.ir.vocal import LyricsLine, VocalNote

logger = structlog.get_logger()


@dataclass(frozen=True)
class VocalSynthConfig:
    """Configuration for a vocal synthesis engine.

    Attributes:
        engine: Engine name ("vocaloid", "cevio", "neutrino", "utau").
        voice_model: Voice model/singer name.
        language: Language code (e.g., "ja", "en").
        tempo_bpm: Tempo for timing calculation.
        output_format: Audio format ("wav", "mp3").
    """

    engine: str
    voice_model: str = "default"
    language: str = "en"
    tempo_bpm: float = 120.0
    output_format: str = "wav"


@dataclass(frozen=True)
class VocalSynthResult:
    """Result from vocal synthesis.

    Attributes:
        audio_path: Path to rendered audio file (None if synthesis failed).
        duration_sec: Duration of rendered audio.
        engine: Engine used for synthesis.
        success: Whether synthesis succeeded.
        error_message: Error message if synthesis failed.
    """

    audio_path: Path | None = None
    duration_sec: float = 0.0
    engine: str = ""
    success: bool = False
    error_message: str = ""


class VocalSynthBridge(ABC):
    """Abstract bridge for vocal synthesis engines.

    Subclass this to implement integration with a specific engine.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the synthesis engine is installed and accessible.

        Returns:
            True if ready to synthesize.
        """

    @abstractmethod
    def synthesize(
        self,
        vocal_notes: tuple[VocalNote, ...],
        lyrics: list[LyricsLine],
        config: VocalSynthConfig,
        output_path: Path,
    ) -> VocalSynthResult:
        """Synthesize vocal audio from notes and lyrics.

        Args:
            vocal_notes: The vocal note sequence.
            lyrics: Lyrics lines with syllable alignment.
            config: Synthesis configuration.
            output_path: Where to write the rendered audio.

        Returns:
            VocalSynthResult with path to rendered audio.
        """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of this synthesis engine."""


class NeutrinoBridge(VocalSynthBridge):
    """Bridge for NEUTRINO vocal synthesis (open-source, Japanese).

    NEUTRINO uses MusicXML input. This bridge converts VocalNote + lyrics
    to MusicXML, invokes NEUTRINO CLI, and returns the rendered WAV.

    Requires NEUTRINO to be installed separately.
    """

    def __init__(self, neutrino_path: Path | None = None) -> None:
        self._neutrino_path = neutrino_path

    @property
    def engine_name(self) -> str:
        """Engine name."""
        return "neutrino"

    def is_available(self) -> bool:
        """Check if NEUTRINO is installed."""
        if self._neutrino_path and self._neutrino_path.exists():
            return True
        logger.info("neutrino_not_found", path=str(self._neutrino_path))
        return False

    def synthesize(
        self,
        vocal_notes: tuple[VocalNote, ...],
        lyrics: list[LyricsLine],
        config: VocalSynthConfig,
        output_path: Path,
    ) -> VocalSynthResult:
        """Synthesize via NEUTRINO.

        Args:
            vocal_notes: The vocal note sequence.
            lyrics: Lyrics lines.
            config: Synthesis configuration.
            output_path: Output audio path.

        Returns:
            VocalSynthResult.
        """
        if not self.is_available():
            return VocalSynthResult(
                engine="neutrino",
                success=False,
                error_message="NEUTRINO is not installed or path is invalid.",
            )

        logger.info(
            "neutrino_synthesize",
            notes=len(vocal_notes),
            lyrics_lines=len(lyrics),
            voice=config.voice_model,
        )

        # Stub: actual NEUTRINO integration requires MusicXML generation
        # and subprocess invocation of NEUTRINO CLI
        return VocalSynthResult(
            engine="neutrino",
            success=False,
            error_message="NEUTRINO synthesis not yet implemented. Install NEUTRINO and contribute the integration.",
        )


class MidiVocalFallback(VocalSynthBridge):
    """Fallback that renders vocal notes as regular MIDI (choir_aahs).

    Always available. Provides a basic vocal representation via GM
    program 52 (Choir Aahs) when no external engine is configured.
    """

    @property
    def engine_name(self) -> str:
        """Engine name."""
        return "midi_fallback"

    def is_available(self) -> bool:
        """Always available."""
        return True

    def synthesize(
        self,
        vocal_notes: tuple[VocalNote, ...],
        lyrics: list[LyricsLine],
        config: VocalSynthConfig,
        output_path: Path,
    ) -> VocalSynthResult:
        """Render vocal notes as MIDI with choir_aahs.

        Args:
            vocal_notes: The vocal note sequence.
            lyrics: Lyrics lines (ignored for MIDI fallback).
            config: Synthesis configuration.
            output_path: Output MIDI path.

        Returns:
            VocalSynthResult.
        """
        logger.info(
            "vocal_midi_fallback",
            notes=len(vocal_notes),
            message="Using MIDI choir_aahs as vocal substitute.",
        )
        # The actual MIDI rendering is handled by midi_writer.py
        # This bridge just signals that fallback mode is active
        return VocalSynthResult(
            engine="midi_fallback",
            success=True,
            error_message="",
        )


# ── Registry ──────────────────────────────────────────────────────────

_BRIDGES: dict[str, type[VocalSynthBridge]] = {
    "neutrino": NeutrinoBridge,
    "midi_fallback": MidiVocalFallback,
}


def get_vocal_bridge(engine: str = "midi_fallback") -> VocalSynthBridge:
    """Get a vocal synthesis bridge by engine name.

    Args:
        engine: Engine name.

    Returns:
        VocalSynthBridge instance.

    Raises:
        ValueError: If engine is unknown.
    """
    bridge_cls = _BRIDGES.get(engine)
    if bridge_cls is None:
        available = list(_BRIDGES.keys())
        msg = f"Unknown vocal engine '{engine}'. Available: {available}"
        raise ValueError(msg)
    return bridge_cls()
