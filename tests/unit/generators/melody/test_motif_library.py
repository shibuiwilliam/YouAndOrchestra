"""Tests for motif library persistence (save/load/list)."""

from __future__ import annotations

from pathlib import Path

import pytest

from yao.generators.melody.motif_library import list_motifs, load_motif, save_motif
from yao.ir.motif import Motif
from yao.ir.note import Note


def _make_motif(pitches: list[int]) -> Motif:
    """Create a simple motif."""
    notes = tuple(
        Note(pitch=p, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano")
        for i, p in enumerate(pitches)
    )
    return Motif(notes=notes, label="test_motif")


class TestMotifLibrary:
    """Tests for motif persistence."""

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        """Saved motif can be loaded back identically."""
        motif = _make_motif([60, 62, 64])
        save_motif(motif, "test_ascending", library_dir=tmp_path)

        loaded = load_motif("test_ascending", library_dir=tmp_path)

        assert len(loaded.notes) == 3
        assert loaded.notes[0].pitch == 60
        assert loaded.notes[1].pitch == 62
        assert loaded.notes[2].pitch == 64
        assert loaded.label == "test_motif"

    def test_save_creates_json_file(self, tmp_path: Path) -> None:
        """Save creates a JSON file in the library directory."""
        motif = _make_motif([60])
        path = save_motif(motif, "single_note", library_dir=tmp_path)

        assert path.exists()
        assert path.suffix == ".json"

    def test_save_updates_catalog(self, tmp_path: Path) -> None:
        """Save updates the catalog YAML."""
        motif = _make_motif([60, 64])
        save_motif(motif, "test_entry", library_dir=tmp_path)

        entries = list_motifs(library_dir=tmp_path)
        assert len(entries) == 1
        assert entries[0]["id"] == "test_entry"

    def test_save_with_metadata(self, tmp_path: Path) -> None:
        """Save with metadata includes it in catalog."""
        motif = _make_motif([60])
        save_motif(
            motif,
            "jazz_lick",
            library_dir=tmp_path,
            metadata={"genre": "bebop_jazz", "description": "ii-V approach"},
        )

        entries = list_motifs(library_dir=tmp_path)
        assert entries[0]["genre"] == "bebop_jazz"

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        """Loading a nonexistent motif raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_motif("nonexistent", library_dir=tmp_path)

    def test_multiple_saves(self, tmp_path: Path) -> None:
        """Multiple saves produce multiple catalog entries."""
        save_motif(_make_motif([60]), "m1", library_dir=tmp_path)
        save_motif(_make_motif([64]), "m2", library_dir=tmp_path)
        save_motif(_make_motif([67]), "m3", library_dir=tmp_path)

        entries = list_motifs(library_dir=tmp_path)
        assert len(entries) == 3

    def test_overwrite_replaces_entry(self, tmp_path: Path) -> None:
        """Saving with the same ID replaces the catalog entry."""
        save_motif(_make_motif([60]), "same_id", library_dir=tmp_path)
        save_motif(_make_motif([72]), "same_id", library_dir=tmp_path)

        entries = list_motifs(library_dir=tmp_path)
        assert len(entries) == 1

        loaded = load_motif("same_id", library_dir=tmp_path)
        assert loaded.notes[0].pitch == 72

    def test_transformations_preserved(self, tmp_path: Path) -> None:
        """Transformation history is preserved through save/load."""
        from yao.ir.motif import transpose

        original = _make_motif([60, 62])
        transformed = transpose(original, 5)
        save_motif(transformed, "transposed", library_dir=tmp_path)

        loaded = load_motif("transposed", library_dir=tmp_path)
        assert "transpose(5)" in loaded.transformations_applied

    def test_empty_catalog(self, tmp_path: Path) -> None:
        """List returns empty for directory with no catalog."""
        entries = list_motifs(library_dir=tmp_path)
        assert entries == []
