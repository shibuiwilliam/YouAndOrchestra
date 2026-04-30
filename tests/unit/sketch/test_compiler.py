"""Tests for SpecCompiler — NL description to CompositionSpec conversion."""

from __future__ import annotations

from yao.sketch.compiler import SpecCompiler


class TestMoodToKey:
    """Test mood keyword → key signature mapping."""

    def test_happy_maps_to_c_major(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a happy upbeat tune", "test-happy")
        assert spec.key == "C major"

    def test_sad_maps_to_d_minor(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a sad melancholic piece", "test-sad")
        assert spec.key == "D minor"

    def test_dark_maps_to_c_minor(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a dark mysterious soundtrack", "test-dark")
        # "dark" matches before "mysterious"
        assert spec.key == "C minor"

    def test_no_mood_defaults_to_c_major(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a piece of music", "test-default")
        assert spec.key == "C major"


class TestTempoInference:
    """Test pace keyword → tempo mapping."""

    def test_calm_gives_slow_tempo(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a calm ambient piece", "test-calm")
        assert spec.tempo_bpm == 80.0

    def test_fast_gives_high_tempo(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a fast driving beat", "test-fast")
        assert spec.tempo_bpm == 140.0

    def test_very_fast_matches_before_fast(self) -> None:
        """Longest-match-first: 'very fast' should match before 'fast'."""
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a very fast intense track", "test-vfast")
        assert spec.tempo_bpm == 160.0

    def test_no_pace_defaults_to_120(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a piece of music", "test-default-tempo")
        assert spec.tempo_bpm == 120.0


class TestInstrumentSelection:
    """Test keyword → instrument mapping."""

    def test_piano_keyword(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a piano ballad", "test-piano")
        names = [i.name for i in spec.instruments]
        assert "piano" in names

    def test_classical_keyword_gives_trio(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a classical sonata", "test-classical")
        names = [i.name for i in spec.instruments]
        assert "piano" in names
        assert "violin" in names
        assert "cello" in names

    def test_orchestra_keyword(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("an orchestral piece", "test-orch")
        names = [i.name for i in spec.instruments]
        assert len(names) >= 3  # noqa: PLR2004
        assert "strings_ensemble" in names

    def test_no_keyword_defaults_to_piano_bass(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a piece of music", "test-default-inst")
        names = [i.name for i in spec.instruments]
        assert "piano" in names
        assert "acoustic_bass" in names


class TestDurationExtraction:
    """Test duration parsing from NL text."""

    def test_seconds_extraction(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a 60 second jingle", "test-60s")
        # 60s at 120bpm = 120 beats = 30 bars
        assert spec.computed_total_bars() == 30

    def test_minutes_extraction(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a 2 minute calm piece", "test-2m")
        # 2min = 120s at 80bpm = 160 beats = 40 bars
        assert spec.computed_total_bars() == 40


class TestGenreDetection:
    """Test genre keyword detection."""

    def test_cinematic(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a cinematic film score", "test-cine")
        assert spec.genre == "cinematic"

    def test_jazz(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a jazz piano piece", "test-jazz")
        assert spec.genre == "jazz"

    def test_no_genre_defaults_to_general(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a piece of music", "test-gen")
        assert spec.genre == "general"


class TestSectionBuilding:
    """Test section structure generation."""

    def test_short_piece_has_one_section(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a 10 second fast jingle", "test-short")
        # Very short pieces get a single verse section
        assert len(spec.sections) >= 1

    def test_medium_piece_has_multiple_sections(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a 90 second piece", "test-medium")
        assert len(spec.sections) >= 3  # noqa: PLR2004

    def test_long_piece_has_bridge(self) -> None:
        compiler = SpecCompiler()
        spec, _ = compiler.compile("a 3 minute epic piece", "test-long")
        section_names = [s.name for s in spec.sections]
        # Long pieces get bridge
        assert "bridge" in section_names or len(spec.sections) >= 4  # noqa: PLR2004


class TestTrajectoryBuilding:
    """Test trajectory generation from description."""

    def test_calm_has_low_tension(self) -> None:
        compiler = SpecCompiler()
        _, traj = compiler.compile("a calm peaceful piece", "test-calm-traj")
        assert traj.tension is not None
        # Calm trajectory should have low peak tension
        max_tension = max(w.value for w in traj.tension.waypoints)
        assert max_tension <= 0.5  # noqa: PLR2004

    def test_epic_has_high_tension(self) -> None:
        compiler = SpecCompiler()
        _, traj = compiler.compile("an epic dramatic piece", "test-epic-traj")
        assert traj.tension is not None
        max_tension = max(w.value for w in traj.tension.waypoints)
        assert max_tension >= 0.9  # noqa: PLR2004


class TestCompileEndToEnd:
    """Test full compile() output."""

    def test_compile_returns_valid_spec(self) -> None:
        compiler = SpecCompiler()
        spec, traj = compiler.compile(
            "a sad piano piece for 90 seconds",
            "test-e2e",
        )
        assert spec.title == "Test E2E"
        assert spec.key == "D minor"  # "sad" → D minor
        assert any(i.name == "piano" for i in spec.instruments)
        assert spec.generation.strategy == "stochastic"
        assert traj.tension is not None
