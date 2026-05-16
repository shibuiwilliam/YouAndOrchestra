"""Tests for the vocal synthesis bridge."""

from __future__ import annotations

import pytest

from yao.render.vocal_synth_bridge import (
    MidiVocalFallback,
    NeutrinoBridge,
    VocalSynthConfig,
    get_vocal_bridge,
)


class TestMidiVocalFallback:
    """Tests for the MIDI fallback bridge."""

    def test_always_available(self) -> None:
        """MIDI fallback should always be available."""
        bridge = MidiVocalFallback()
        assert bridge.is_available()

    def test_engine_name(self) -> None:
        """Engine name should be midi_fallback."""
        bridge = MidiVocalFallback()
        assert bridge.engine_name == "midi_fallback"

    def test_synthesize_returns_success(self) -> None:
        """Synthesize should return success (it's a passthrough)."""
        bridge = MidiVocalFallback()
        config = VocalSynthConfig(engine="midi_fallback")
        result = bridge.synthesize((), [], config, output_path=None)
        assert result.success
        assert result.engine == "midi_fallback"


class TestNeutrinoBridge:
    """Tests for the NEUTRINO bridge stub."""

    def test_not_available_without_path(self) -> None:
        """NEUTRINO should not be available without valid path."""
        bridge = NeutrinoBridge(neutrino_path=None)
        assert not bridge.is_available()

    def test_engine_name(self) -> None:
        """Engine name should be neutrino."""
        bridge = NeutrinoBridge()
        assert bridge.engine_name == "neutrino"

    def test_synthesize_fails_when_unavailable(self) -> None:
        """Synthesize should fail gracefully when NEUTRINO is not installed."""
        bridge = NeutrinoBridge(neutrino_path=None)
        config = VocalSynthConfig(engine="neutrino")
        result = bridge.synthesize((), [], config, output_path=None)
        assert not result.success
        assert "not installed" in result.error_message


class TestGetVocalBridge:
    """Tests for the bridge registry."""

    def test_get_midi_fallback(self) -> None:
        """Should return MidiVocalFallback."""
        bridge = get_vocal_bridge("midi_fallback")
        assert isinstance(bridge, MidiVocalFallback)

    def test_get_neutrino(self) -> None:
        """Should return NeutrinoBridge."""
        bridge = get_vocal_bridge("neutrino")
        assert isinstance(bridge, NeutrinoBridge)

    def test_unknown_engine_raises(self) -> None:
        """Unknown engine should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown vocal engine"):
            get_vocal_bridge("nonexistent_engine")
