"""Motif library persistence — save and load reusable motifs.

Motifs are stored as JSON files in ``references/motifs/`` with
metadata in ``references/motifs/catalog.yaml``. This enables
motifs to be reused across compositions and shared between projects.

See IMPROVEMENT.md §4.3 (Motif Library Persistence).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from yao.ir.motif import Motif
from yao.ir.note import Note


def _default_library_dir() -> Path:
    """Return the default motif library directory."""
    return Path(__file__).resolve().parent.parent.parent.parent / "references" / "motifs"


def save_motif(
    motif: Motif,
    motif_id: str,
    *,
    library_dir: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Save a motif to the library.

    Args:
        motif: The motif to save.
        motif_id: Unique identifier for the motif.
        library_dir: Directory to save to. Defaults to references/motifs/.
        metadata: Additional metadata (genre, description, etc.).

    Returns:
        Path to the saved JSON file.
    """
    if library_dir is None:
        library_dir = _default_library_dir()
    library_dir.mkdir(parents=True, exist_ok=True)

    # Serialize motif to JSON
    motif_data: dict[str, Any] = {
        "id": motif_id,
        "label": motif.label,
        "transformations_applied": list(motif.transformations_applied),
        "notes": [
            {
                "pitch": n.pitch,
                "start_beat": n.start_beat,
                "duration_beats": n.duration_beats,
                "velocity": n.velocity,
                "instrument": n.instrument,
            }
            for n in motif.notes
        ],
    }
    if metadata:
        motif_data["metadata"] = metadata

    json_path = library_dir / f"{motif_id}.json"
    with open(json_path, "w") as f:
        json.dump(motif_data, f, indent=2)

    # Update catalog
    _update_catalog(library_dir, motif_id, motif.label, metadata)

    return json_path


def load_motif(
    motif_id: str,
    *,
    library_dir: Path | None = None,
) -> Motif:
    """Load a motif from the library.

    Args:
        motif_id: Identifier of the motif to load.
        library_dir: Directory to load from. Defaults to references/motifs/.

    Returns:
        The loaded Motif.

    Raises:
        FileNotFoundError: If the motif file doesn't exist.
    """
    if library_dir is None:
        library_dir = _default_library_dir()

    json_path = library_dir / f"{motif_id}.json"
    with open(json_path) as f:
        data = json.load(f)

    notes = tuple(
        Note(
            pitch=n["pitch"],
            start_beat=n["start_beat"],
            duration_beats=n["duration_beats"],
            velocity=n["velocity"],
            instrument=n["instrument"],
        )
        for n in data["notes"]
    )

    return Motif(
        notes=notes,
        label=data.get("label", motif_id),
        transformations_applied=tuple(data.get("transformations_applied", ())),
    )


def list_motifs(
    *,
    library_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """List all motifs in the library catalog.

    Args:
        library_dir: Directory to scan. Defaults to references/motifs/.

    Returns:
        List of motif catalog entries.
    """
    if library_dir is None:
        library_dir = _default_library_dir()

    catalog_path = library_dir / "catalog.yaml"
    if not catalog_path.exists():
        return []

    with open(catalog_path) as f:
        data = yaml.safe_load(f)

    if not data or not isinstance(data.get("motifs"), list):
        return []

    return list(data["motifs"])


def _update_catalog(
    library_dir: Path,
    motif_id: str,
    label: str,
    metadata: dict[str, Any] | None,
) -> None:
    """Update the catalog YAML with a new or updated entry.

    Args:
        library_dir: Library directory.
        motif_id: Motif identifier.
        label: Motif label.
        metadata: Optional metadata.
    """
    catalog_path = library_dir / "catalog.yaml"

    if catalog_path.exists():
        with open(catalog_path) as f:
            catalog = yaml.safe_load(f) or {}
    else:
        catalog = {}

    motifs = catalog.get("motifs", [])
    if not isinstance(motifs, list):
        motifs = []

    # Remove existing entry with same ID
    motifs = [m for m in motifs if m.get("id") != motif_id]

    entry: dict[str, Any] = {
        "id": motif_id,
        "label": label,
        "file": f"{motif_id}.json",
    }
    if metadata:
        entry.update(metadata)
    motifs.append(entry)

    catalog["motifs"] = motifs
    with open(catalog_path, "w") as f:
        yaml.dump(catalog, f, default_flow_style=False, sort_keys=False)
