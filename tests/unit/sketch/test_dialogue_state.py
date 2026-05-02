"""Tests for sketch dialogue state persistence — Wave 3.6.

Verifies save/load/resume of multi-turn /sketch dialogue state.
"""

from __future__ import annotations

from pathlib import Path

from yao.sketch.dialogue_state import SketchState


class TestSketchStatePersistence:
    """Tests for save/load cycle."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        state = SketchState(project_name="test-song", turn=2, emotion="calm")
        path = state.save(tmp_path)
        assert path.exists()
        assert path.name == "sketch_state.json"

    def test_load_restores_state(self, tmp_path: Path) -> None:
        original = SketchState(
            project_name="cafe-rain",
            turn=3,
            emotion="melancholic",
            purpose="study bgm",
            key="D minor",
            tempo_bpm=72.0,
            instruments=[{"name": "piano", "role": "melody"}],
            sections=[{"name": "intro", "bars": 4}, {"name": "verse", "bars": 8}],
        )
        original.save(tmp_path)
        loaded = SketchState.load(tmp_path)
        assert loaded.project_name == "cafe-rain"
        assert loaded.turn == 3
        assert loaded.emotion == "melancholic"
        assert loaded.key == "D minor"
        assert loaded.instruments == [{"name": "piano", "role": "melody"}]
        assert len(loaded.sections) == 2

    def test_exists_check(self, tmp_path: Path) -> None:
        assert not SketchState.exists(tmp_path)
        SketchState(project_name="x").save(tmp_path)
        assert SketchState.exists(tmp_path)

    def test_advance_turn(self) -> None:
        state = SketchState(turn=1)
        state.advance_turn()
        assert state.turn == 2
        state.turn = 6
        state.advance_turn()
        assert state.turn == 6  # capped at 6

    def test_is_complete(self) -> None:
        state = SketchState(turn=5)
        assert not state.is_complete()
        state.turn = 6
        assert state.is_complete()


class TestSketchStateDialogueFlow:
    """Test the full 6-turn dialogue state progression."""

    def test_full_dialogue_flow(self, tmp_path: Path) -> None:
        """Simulate a complete 6-turn dialogue."""
        state = SketchState(project_name="my-song")

        # Turn 1: emotion/purpose
        assert state.turn == 1
        state.emotion = "nostalgic"
        state.purpose = "personal listening"
        state.context = "evening, headphones"
        state.advance_turn()
        state.save(tmp_path)

        # Turn 2: references
        assert state.turn == 2
        state.like_references = ["Debussy", "Satie"]
        state.avoid_references = ["heavy metal"]
        state.advance_turn()
        state.save(tmp_path)

        # Turn 3: instruments/structure
        assert state.turn == 3
        state.instruments = [{"name": "piano", "role": "melody"}, {"name": "cello", "role": "bass"}]
        state.duration_seconds = 90.0
        state.key = "F major"
        state.tempo_bpm = 80.0
        state.sections = [
            {"name": "intro", "bars": 4},
            {"name": "verse", "bars": 8},
            {"name": "chorus", "bars": 8},
            {"name": "outro", "bars": 4},
        ]
        state.advance_turn()
        state.save(tmp_path)

        # Turn 4: trajectory
        assert state.turn == 4
        state.trajectory_waypoints = [[0, 0.2], [8, 0.5], [16, 0.8], [24, 0.2]]
        state.climax_section = "chorus"
        state.advance_turn()
        state.save(tmp_path)

        # Turn 5: confirmation
        assert state.turn == 5
        state.advance_turn()
        state.save(tmp_path)

        # Turn 6: generation
        assert state.turn == 6
        assert state.is_complete()

        # Verify resume from any point
        loaded = SketchState.load(tmp_path)
        assert loaded.turn == 6
        assert loaded.key == "F major"
        assert loaded.climax_section == "chorus"
        assert len(loaded.trajectory_waypoints) == 4

    def test_resume_from_mid_dialogue(self, tmp_path: Path) -> None:
        """Simulate interruption and resume."""
        state = SketchState(project_name="interrupted", turn=3, emotion="tense", key="C minor")
        state.save(tmp_path)

        # Simulate new session
        resumed = SketchState.load(tmp_path)
        assert resumed.turn == 3
        assert resumed.project_name == "interrupted"
        assert resumed.emotion == "tense"
        assert resumed.key == "C minor"


class TestSketchStateSummary:
    """Tests for summary formatting."""

    def test_summary_shows_turn(self) -> None:
        state = SketchState(project_name="test", turn=3)
        assert "Turn 3/6" in state.summary()

    def test_summary_shows_key_info(self) -> None:
        state = SketchState(
            project_name="demo",
            turn=4,
            emotion="calm",
            key="G major",
            tempo_bpm=90.0,
            instruments=[{"name": "piano", "role": "melody"}],
        )
        s = state.summary()
        assert "calm" in s
        assert "G major" in s
        assert "piano" in s
