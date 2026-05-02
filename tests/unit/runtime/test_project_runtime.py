"""Tests for ProjectRuntime — cache, undo/redo, lockfile."""

from __future__ import annotations

from pathlib import Path

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.runtime.project_runtime import ProjectRuntime


def _make_score(title: str = "Test") -> ScoreIR:
    notes = (Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),)
    return ScoreIR(
        title=title,
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="v", start_bar=0, end_bar=1, parts=(Part(instrument="piano", notes=notes),)),),
    )


class TestProjectRuntime:
    def test_context_manager(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            assert rt.project_name == "test"
        assert not (tmp_path / "proj" / ".lock").exists()

    def test_set_score(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            rt.set_score(_make_score("v1"), "initial")
            assert rt.current_score is not None
            assert rt.current_score.title == "v1"

    def test_undo_redo(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            rt.set_score(_make_score("v1"), "v1")
            rt.set_score(_make_score("v2"), "v2")
            assert rt.can_undo
            state = rt.undo()
            assert state is not None
            assert rt.can_redo

    def test_redo_cleared_on_new_edit(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            rt.set_score(_make_score("v1"), "v1")
            rt.set_score(_make_score("v2"), "v2")
            rt.undo()
            assert rt.can_redo
            rt.set_score(_make_score("v3"), "v3")
            assert not rt.can_redo

    def test_undo_stack_capped(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            for i in range(60):
                rt.set_score(_make_score(f"v{i}"), f"v{i}")
            assert rt.undo_depth <= 50

    def test_cache_round_trip(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            midi = tmp_path / "test.mid"
            midi.write_bytes(b"fake midi")
            rt.save_to_cache("hash1", 42, "rule_based", midi)
            cached = rt.get_cached("hash1", 42, "rule_based")
            assert cached is not None
            assert cached.exists()

    def test_cache_miss(self, tmp_path: Path) -> None:
        with ProjectRuntime("test", base_dir=tmp_path / "proj") as rt:
            assert rt.get_cached("nonexistent", 0, "x") is None
