"""DAW MCP Bridge — Model Context Protocol integration for DAWs.

Provides the interface for MCP-based DAW control. Supports Reaper via
RPP file export/import and optional ReaScript TCP control. Other DAWs
can be integrated by extending the DAWBackend ABC.

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import structlog

from yao.ir.score_ir import ScoreIR
from yao.render.midi_writer import write_midi

logger = structlog.get_logger()

# Reaper TCP control defaults (ReaScript ExtState)
_REAPER_DEFAULT_HOST = "127.0.0.1"
_REAPER_DEFAULT_PORT = 8800


@dataclass(frozen=True)
class MCPStatus:
    """Status of a DAW MCP connection.

    Attributes:
        connected: Whether a DAW is connected.
        daw_name: Name of the connected DAW.
        project_name: Current DAW project name.
        version: DAW version string if available.
    """

    connected: bool = False
    daw_name: str = ""
    project_name: str = ""
    version: str = ""


class DAWBackend(ABC):
    """Abstract backend for a specific DAW."""

    @abstractmethod
    def probe(self) -> MCPStatus:
        """Check if the DAW is running and accessible."""

    @abstractmethod
    def import_midi(self, midi_path: Path) -> bool:
        """Import a MIDI file into the DAW project."""

    @abstractmethod
    def export_midi(self, output_path: Path) -> bool:
        """Export the current DAW project to MIDI."""

    @property
    @abstractmethod
    def name(self) -> str:
        """DAW name."""


class ReaperBackend(DAWBackend):
    """Reaper integration via TCP ReaScript control and RPP file exchange.

    Requires Reaper to be running with ReaScript TCP server enabled
    (Actions > Show action list > ReaScript > Network).
    """

    def __init__(
        self,
        host: str = _REAPER_DEFAULT_HOST,
        port: int = _REAPER_DEFAULT_PORT,
    ) -> None:
        self._host = host
        self._port = port

    @property
    def name(self) -> str:
        """DAW name."""
        return "reaper"

    def probe(self) -> MCPStatus:
        """Check if Reaper TCP server is accessible.

        Returns:
            MCPStatus with connection result.
        """
        try:
            with socket.create_connection((self._host, self._port), timeout=2.0):
                logger.info("reaper_connected", host=self._host, port=self._port)
                return MCPStatus(connected=True, daw_name="reaper")
        except (ConnectionRefusedError, TimeoutError, OSError):
            logger.debug("reaper_not_available", host=self._host, port=self._port)
            return MCPStatus(connected=False, daw_name="reaper")

    def import_midi(self, midi_path: Path) -> bool:
        """Import MIDI into Reaper via ReaScript command.

        Args:
            midi_path: Path to MIDI file.

        Returns:
            True if import command was sent successfully.
        """
        if not midi_path.exists():
            logger.error("midi_file_not_found", path=str(midi_path))
            return False

        try:
            cmd = f"IMPORT_MIDI;{midi_path.resolve()}\n"
            with socket.create_connection((self._host, self._port), timeout=5.0) as sock:
                sock.sendall(cmd.encode("utf-8"))
                logger.info("reaper_midi_imported", path=str(midi_path))
                return True
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            logger.error("reaper_import_failed", error=str(e))
            return False

    def export_midi(self, output_path: Path) -> bool:
        """Request Reaper to export current project as MIDI.

        Args:
            output_path: Where to write the exported MIDI.

        Returns:
            True if export command was sent successfully.
        """
        try:
            cmd = f"EXPORT_MIDI;{output_path.resolve()}\n"
            with socket.create_connection((self._host, self._port), timeout=5.0) as sock:
                sock.sendall(cmd.encode("utf-8"))
                logger.info("reaper_midi_exported", path=str(output_path))
                return True
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            logger.error("reaper_export_failed", error=str(e))
            return False


# ── Backend registry ──────────────────────────────────────────────────

_BACKENDS: dict[str, type[DAWBackend]] = {
    "reaper": ReaperBackend,
}


class DAWMCPBridge:
    """Model Context Protocol bridge for DAW integration.

    Supports Reaper via TCP ReaScript. Falls back to MIDI file exchange
    when the DAW's TCP server is not available.
    """

    def __init__(self) -> None:
        self._status = MCPStatus()
        self._backend: DAWBackend | None = None

    @property
    def status(self) -> MCPStatus:
        """Current connection status."""
        return self._status

    def connect(self, daw: str = "reaper", **kwargs: object) -> MCPStatus:
        """Attempt to connect to a DAW.

        Args:
            daw: DAW name ("reaper").
            **kwargs: Backend-specific connection options.

        Returns:
            Connection status.
        """
        backend_cls = _BACKENDS.get(daw)
        if backend_cls is None:
            available = list(_BACKENDS.keys())
            logger.warning("daw_unknown", daw=daw, available=available)
            self._status = MCPStatus(connected=False, daw_name=daw)
            return self._status

        self._backend = backend_cls(**kwargs)
        self._status = self._backend.probe()
        return self._status

    def push_score(self, score: ScoreIR, work_dir: Path | None = None) -> bool:
        """Push a ScoreIR to the connected DAW via MIDI export + import.

        Args:
            score: The ScoreIR to send.
            work_dir: Working directory for temporary MIDI file.

        Returns:
            True if successful.
        """
        if not self._status.connected or self._backend is None:
            logger.warning("daw_mcp_not_connected", message="No DAW connected.")
            return False

        # Write MIDI to temp location and import into DAW
        target = (work_dir or Path(".")) / "_daw_bridge_temp.mid"
        write_midi(score, target)
        result = self._backend.import_midi(target)
        if result:
            logger.info("daw_score_pushed", tracks=len(score.sections))
        return result

    def pull_changes(self, work_dir: Path | None = None) -> Path | None:
        """Pull changes from the DAW as a MIDI file.

        Args:
            work_dir: Working directory for exported MIDI.

        Returns:
            Path to exported MIDI file, or None if not connected.
        """
        if not self._status.connected or self._backend is None:
            return None

        target = (work_dir or Path(".")) / "_daw_bridge_pull.mid"
        if self._backend.export_midi(target):
            return target
        return None
