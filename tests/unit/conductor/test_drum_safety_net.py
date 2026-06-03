"""Tests for Conductor drum safety net logic."""

from __future__ import annotations

from yao.conductor.conductor import Conductor
from yao.schema.composition import CompositionSpec, InstrumentSpec, SectionSpec


def _make_spec(genre: str = "pop_mainstream", tempo: float = 120.0) -> CompositionSpec:
    return CompositionSpec(
        title="test",
        genre=genre,
        tempo_bpm=tempo,
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="verse", bars=8, dynamics="mf")],
    )


class TestDrumSafetyNet:
    """Test _needs_drum_safety_net and _safety_net_drum_pattern."""

    def test_ambient_does_not_need_drums(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="ambient", tempo=80.0)
        assert conductor._needs_drum_safety_net(spec) is False

    def test_classical_does_not_need_drums(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="classical_romantic", tempo=90.0)
        assert conductor._needs_drum_safety_net(spec) is False

    def test_pop_needs_drums(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="pop_mainstream", tempo=120.0)
        assert conductor._needs_drum_safety_net(spec) is True

    def test_rock_needs_drums(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="rock_classic", tempo=130.0)
        assert conductor._needs_drum_safety_net(spec) is True

    def test_very_slow_tempo_no_drums(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="pop_mainstream", tempo=50.0)
        assert conductor._needs_drum_safety_net(spec) is False

    def test_safety_net_returns_pattern(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="pop_mainstream", tempo=120.0)
        pattern = conductor._safety_net_drum_pattern(spec)
        assert pattern is not None
        assert isinstance(pattern, str)

    def test_safety_net_slow_tempo(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="pop_mainstream", tempo=70.0)
        pattern = conductor._safety_net_drum_pattern(spec)
        assert pattern is not None

    def test_safety_net_fast_tempo(self) -> None:
        conductor = Conductor()
        spec = _make_spec(genre="metal", tempo=160.0)
        pattern = conductor._safety_net_drum_pattern(spec)
        assert pattern is not None
