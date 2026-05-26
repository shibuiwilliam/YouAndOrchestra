"""Integration test: composition with drum pattern.

Verifies that a spec with `drums:` produces a MIDI file containing
a drum track, that specs without `drums:` remain unchanged, and that
beat-based genres auto-attach drums when `drums:` is unspecified.
"""

from __future__ import annotations

from pathlib import Path

import pretty_midi

# Ensure generators are registered
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.drum_patterner import drums_spec_from_genre, generate_drum_hits
from yao.generators.registry import get_generator
from yao.render.midi_writer import write_midi
from yao.schema.composition import (
    CompositionSpec,
    DrumsSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


class TestComposeWithDrums:
    """End-to-end: spec with drums produces MIDI with drum track."""

    def test_lofi_spec_has_drum_track(self, tmp_path: Path) -> None:
        """A spec with drums: should produce a MIDI with a drum instrument."""
        spec = CompositionSpec(
            title="Lofi Test",
            key="A minor",
            tempo_bpm=82,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mp")],
            drums=DrumsSpec(pattern_family="lofi_laidback", swing=0.6),
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        # Generate pitched notes
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)

        # Generate drum hits
        drum_hits, _ = generate_drum_hits(spec, seed=42)
        assert len(drum_hits) > 0

        # Write MIDI with drums
        out = tmp_path / "with_drums.mid"
        write_midi(score, out, drum_hits=drum_hits)
        assert out.exists()

        # Verify MIDI has a drum instrument
        midi = pretty_midi.PrettyMIDI(str(out))
        drum_instruments = [i for i in midi.instruments if i.is_drum]
        assert len(drum_instruments) == 1
        assert len(drum_instruments[0].notes) > 0

    def test_no_drums_spec_has_no_drum_track(self, tmp_path: Path) -> None:
        """A spec without drums: should produce MIDI without drum track."""
        spec = CompositionSpec(
            title="No Drums",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="mf")],
            generation=GenerationConfig(strategy="rule_based"),
        )

        gen = get_generator("rule_based")
        score, _ = gen.generate(spec)

        out = tmp_path / "no_drums.mid"
        write_midi(score, out)
        assert out.exists()

        midi = pretty_midi.PrettyMIDI(str(out))
        drum_instruments = [i for i in midi.instruments if i.is_drum]
        assert len(drum_instruments) == 0

    def test_rock_auto_attaches_drums_without_spec(self, tmp_path: Path) -> None:
        """A rock spec without drums: should auto-attach drums from genre profile."""
        spec = CompositionSpec(
            title="Rock Auto Drums",
            genre="rock_classic",
            key="E minor",
            tempo_bpm=120,
            instruments=[InstrumentSpec(name="electric_guitar", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="f")],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        assert spec.drums is None, "Spec should have no explicit drums"

        # Genre should resolve to drums
        auto_drums = drums_spec_from_genre(spec.genre)
        assert auto_drums is not None, "rock_classic should auto-attach drums"
        assert auto_drums.pattern_family == "rock_backbeat"

        # Generate with auto drums
        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        drum_spec = spec.model_copy(update={"drums": auto_drums})
        drum_hits, _ = generate_drum_hits(drum_spec, seed=42)
        assert len(drum_hits) > 0

        # Write MIDI
        out = tmp_path / "rock_auto_drums.mid"
        write_midi(score, out, drum_hits=drum_hits)

        # Verify drum track on channel 10
        midi = pretty_midi.PrettyMIDI(str(out))
        drum_instruments = [i for i in midi.instruments if i.is_drum]
        assert len(drum_instruments) == 1
        assert len(drum_instruments[0].notes) > 0

    def test_ambient_does_not_auto_attach_drums(self) -> None:
        """Ambient genre should NOT auto-attach drums."""
        auto_drums = drums_spec_from_genre("ambient")
        assert auto_drums is None, "ambient should not auto-attach drums"

    def test_cinematic_does_not_auto_attach_drums(self) -> None:
        """Cinematic genre should NOT auto-attach drums."""
        auto_drums = drums_spec_from_genre("cinematic")
        assert auto_drums is None, "cinematic should not auto-attach drums"

    def test_all_beat_genres_have_valid_patterns(self) -> None:
        """Every genre with requires_drums=True must map to an existing pattern."""
        from yao.constants.genre_profile import all_genre_profiles
        from yao.generators.drum_patterner import PATTERNS_DIR

        for name, profile in all_genre_profiles().items():
            if profile.requires_drums:
                assert profile.default_drum_pattern is not None, (
                    f"Genre '{name}' requires_drums but has no default_drum_pattern"
                )
                pattern_path = PATTERNS_DIR / f"{profile.default_drum_pattern}.yaml"
                assert pattern_path.exists(), (
                    f"Genre '{name}' references pattern '{profile.default_drum_pattern}' which does not exist"
                )
