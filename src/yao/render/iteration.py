"""Iteration management — versioned output directories.

CLAUDE.md §12: iterations use 3-digit zero-padded versioning (v001, v002, ...).
Output structure: outputs/projects/<project>/iterations/v<NNN>/
"""

from __future__ import annotations

import re
from pathlib import Path

_VERSION_PATTERN = re.compile(r"^v(\d{3})$")


def next_iteration_dir(project_output_dir: Path) -> Path:
    """Determine the next iteration directory path.

    Scans existing iteration directories and returns the path for
    the next version number.

    Args:
        project_output_dir: Path to the project output directory
            (e.g., outputs/projects/my-song/).

    Returns:
        Path to the next iteration directory (e.g., .../iterations/v002/).
    """
    iterations_dir = project_output_dir / "iterations"
    iterations_dir.mkdir(parents=True, exist_ok=True)

    existing = list_iterations(project_output_dir)
    if not existing:
        return iterations_dir / "v001"

    last = existing[-1]
    match = _VERSION_PATTERN.match(last.name)
    next_num = int(match.group(1)) + 1 if match else 1

    return iterations_dir / f"v{next_num:03d}"


def list_iterations(project_output_dir: Path) -> list[Path]:
    """List all existing iteration directories, sorted by version number.

    Args:
        project_output_dir: Path to the project output directory.

    Returns:
        Sorted list of iteration directory paths.
    """
    iterations_dir = project_output_dir / "iterations"
    if not iterations_dir.exists():
        return []

    versions: list[tuple[int, Path]] = []
    for entry in iterations_dir.iterdir():
        if entry.is_dir():
            match = _VERSION_PATTERN.match(entry.name)
            if match:
                versions.append((int(match.group(1)), entry))

    versions.sort(key=lambda x: x[0])
    return [path for _, path in versions]


def current_iteration(project_output_dir: Path) -> Path | None:
    """Return the latest iteration directory, or None if none exist.

    Args:
        project_output_dir: Path to the project output directory.

    Returns:
        Path to the latest iteration, or None.
    """
    iterations = list_iterations(project_output_dir)
    return iterations[-1] if iterations else None
