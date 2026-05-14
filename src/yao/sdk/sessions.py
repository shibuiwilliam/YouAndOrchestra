"""Project-scoped session helpers for YaO.

Wraps the Claude Agent SDK session management with YaO conventions:
- One session directory per project (keyed by absolute path)
- Auto-tagging with iteration versions
- Fork support for "what if" experiments
"""

from __future__ import annotations

from pathlib import Path

from claude_agent_sdk import (
    SDKSessionInfo,
    list_sessions,
    tag_session,
)


def list_project_sessions(
    project_root: Path,
    *,
    limit: int = 10,
) -> list[SDKSessionInfo]:
    """List sessions for a YaO project.

    Args:
        project_root: Absolute path to the project root.
        limit: Maximum number of sessions to return.

    Returns:
        List of session entries, most recent first.
    """
    results: list[SDKSessionInfo] = list_sessions(directory=str(project_root))
    return results[:limit]


def tag_session_with_iteration(
    session_id: str,
    iteration: str,
    *,
    project_root: Path | None = None,
) -> None:
    """Tag a session with the iteration version it ended on.

    Args:
        session_id: The session ID to tag.
        iteration: Iteration name (e.g., "v003").
        project_root: Optional project root for directory context.
    """
    tag_session(
        session_id=session_id,
        tag=iteration,
        directory=str(project_root) if project_root else None,
    )


def session_project_key(project_root: Path) -> str:
    """Generate a stable session key for a project directory.

    Args:
        project_root: Absolute path to the project root.

    Returns:
        A string key suitable for session lookup.
    """
    return str(project_root.resolve())
