"""DAW MCP Bridge — Model Context Protocol integration for DAWs.

Stub implementation. Provides the interface for MCP-based DAW control.
Reaper-first via ReaScript.

Belongs to Layer 5 (Rendering).
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from yao.ir.score_ir import ScoreIR

logger = structlog.get_logger()


@dataclass(frozen=True)
class MCPStatus:
    """Status of a DAW MCP connection.

    Attributes:
        connected: Whether a DAW is connected.
        daw_name: Name of the connected DAW.
        project_name: Current DAW project name.
    """

    connected: bool = False
    daw_name: str = ""
    project_name: str = ""


class DAWMCPBridge:
    """Model Context Protocol bridge for DAW integration.

    Stub implementation. Full Reaper integration in future PR.
    """

    def __init__(self) -> None:
        self._status = MCPStatus()

    @property
    def status(self) -> MCPStatus:
        """Current connection status."""
        return self._status

    def connect(self, daw: str = "reaper") -> MCPStatus:
        """Attempt to connect to a DAW.

        Args:
            daw: DAW name ("reaper", "ableton", "studio_one").

        Returns:
            Connection status.
        """
        logger.info("daw_mcp_connect_attempt", daw=daw)
        # Stub: always returns disconnected
        self._status = MCPStatus(connected=False, daw_name=daw)
        logger.warning(
            "daw_mcp_not_implemented",
            message=f"MCP bridge for {daw} is not yet implemented.",
        )
        return self._status

    def push_score(self, score: ScoreIR) -> bool:
        """Push a ScoreIR to the connected DAW.

        Args:
            score: The ScoreIR to send.

        Returns:
            True if successful, False otherwise.
        """
        if not self._status.connected:
            logger.warning("daw_mcp_not_connected", message="No DAW connected.")
            return False
        return False

    def pull_changes(self) -> ScoreIR | None:
        """Pull changes from the DAW back to ScoreIR.

        Returns:
            Updated ScoreIR, or None if not connected.
        """
        if not self._status.connected:
            return None
        return None
