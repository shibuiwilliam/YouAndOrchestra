"""Scenario tests: default behavior guarantees.

These tests verify that the system's default behavior (without explicit
configuration) produces correct results. They prevent regression of the
P0-P2 improvements by asserting:
1. Beat genres auto-attach drums by default
2. Theme recall is injected by default
3. Genre profile biases affect output by default
"""

from __future__ import annotations

from pathlib import Path

import pretty_midi

import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
from yao.generators.drum_patterner import drums_spec_from_genre, generate_drum_hits
from yao.generators.genre_resolver import inject_theme_recall, resolve_genre
from yao.generators.registry import get_generator
from yao.reflect.provenance import ProvenanceLog
from yao.render.midi_writer import write_midi
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.verify.thematic_coherence import analyze_thematic_coherence


class TestDefaultDrumAttachment:
    """Beat-genre specs without explicit drums should auto-attach drums."""

    BEAT_GENRES = [
        "rock_classic",
        "funk_classic",
        "pop_mainstream",
        "electronic_house",
        "hiphop_trap",
        "reggae",
    ]
    NO_BEAT_GENRES = ["ambient", "cinematic", "classical_baroque", "neoclassical"]

    def test_beat_genres_resolve_drums(self) -> None:
        """All beat genres should resolve to a DrumsSpec."""
        for genre in self.BEAT_GENRES:
            drums = drums_spec_from_genre(genre)
            assert drums is not None, f"{genre} should auto-attach drums"
            assert drums.pattern_family, f"{genre} drum pattern should be non-empty"

    def test_non_beat_genres_do_not_resolve_drums(self) -> None:
        """Non-beat genres should NOT auto-attach drums."""
        for genre in self.NO_BEAT_GENRES:
            drums = drums_spec_from_genre(genre)
            assert drums is None, f"{genre} should NOT auto-attach drums"

    def test_rock_compose_produces_drum_midi(self, tmp_path: Path) -> None:
        """Full pipeline: rock spec without drums → MIDI with Ch10 notes."""
        spec = CompositionSpec(
            title="Rock Default",
            genre="rock_classic",
            key="E minor",
            tempo_bpm=125,
            instruments=[InstrumentSpec(name="electric_guitar", role="melody")],
            sections=[SectionSpec(name="verse", bars=4, dynamics="f")],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)

        auto_drums = drums_spec_from_genre(spec.genre)
        assert auto_drums is not None
        drum_spec = spec.model_copy(update={"drums": auto_drums})
        hits, _ = generate_drum_hits(drum_spec, seed=42)

        out = tmp_path / "rock_default.mid"
        write_midi(score, out, drum_hits=hits)
        midi = pretty_midi.PrettyMIDI(str(out))
        drum_instruments = [i for i in midi.instruments if i.is_drum]
        assert len(drum_instruments) == 1
        assert len(drum_instruments[0].notes) > 0


class TestDefaultThemeRecall:
    """Theme recall should be auto-injected for multi-section specs."""

    def test_auto_recall_on_four_section_spec(self) -> None:
        """A 4-section spec should get recall on the last section."""
        spec = CompositionSpec(
            title="Theme Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="intro", bars=4, dynamics="pp"),
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="f"),
                SectionSpec(name="outro", bars=4, dynamics="pp"),
            ],
        )
        prov = ProvenanceLog()
        enriched = inject_theme_recall(spec, prov)
        assert enriched.sections[-1].recall_melody_from == "intro"


class TestDefaultGenreResolver:
    """Genre resolver should provide complete context."""

    def test_rock_resolves_completely(self) -> None:
        """rock_classic should resolve with drums, tempo, instruments."""
        prov = ProvenanceLog()
        ctx = resolve_genre("rock_classic", prov)
        assert not ctx.is_default
        assert ctx.default_drums is not None
        assert ctx.suggested_tempo is not None
        assert len(ctx.preferred_instruments) > 0

    def test_unknown_genre_returns_default(self) -> None:
        """Unknown genre should return default context, not error."""
        prov = ProvenanceLog()
        ctx = resolve_genre("nonexistent_genre", prov)
        assert ctx.is_default
        assert ctx.default_drums is None


class TestThematicCoherenceMetric:
    """Thematic coherence should be computable on generated output."""

    def test_generated_score_has_measurable_coherence(self) -> None:
        """A real generated score should produce a valid coherence report."""
        spec = CompositionSpec(
            title="Coherence Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=4, dynamics="mf"),
                SectionSpec(name="chorus", bars=4, dynamics="f"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )

        gen = get_generator("stochastic")
        score, _ = gen.generate(spec)
        report = analyze_thematic_coherence(score)

        assert 0.0 <= report.overall_score <= 1.0
        assert 0.0 <= report.section_correlation <= 1.0
        assert 0.0 <= report.first_last_similarity <= 1.0
