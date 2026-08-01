"""Melodic variation & genre character tests.

Guards two related fixes for "the melody is always the same one-pattern loop":

1. Return sections now *develop* the theme (genre-aware variation) instead of
   copying it note-for-note. A′ must stay recognizable (same length, anchored
   endpoints, high overlap) yet differ from A.
2. The melodic line adapts to genre: stepwise genres (ambient) keep a smaller
   average interval than leapy genres (classical), and the theme-development
   amount scales with the genre's melodic freedom.
"""

from __future__ import annotations

import random

from yao.constants.genre_profile import get_genre_profile
from yao.generators.legacy_adapter import generate_via_v2_pipeline
from yao.generators.note.accompaniment import develop_melody, genre_melodic_variation
from yao.ir.note import Note
from yao.ir.plan.harmony import ChordEvent, HarmonicFunction
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)


def _theme() -> list[Note]:
    # A short ascending-then-turning phrase in D minor.
    pitches = [62, 65, 69, 67, 65, 64, 62, 65, 67, 69]
    return [
        Note(pitch=p, start_beat=float(i), duration_beats=1.0, velocity=80, instrument="piano")
        for i, p in enumerate(pitches)
    ]


def _chords() -> list[ChordEvent]:
    return [
        ChordEvent(
            section_id="A2",
            start_beat=b,
            duration_beats=4.0,
            roman="i",
            function=HarmonicFunction.TONIC,
            tension_level=0.3,
        )
        for b in (0.0, 4.0, 8.0)
    ]


class TestDevelopMelody:
    def test_zero_variation_is_exact_restatement(self) -> None:
        theme = _theme()
        out = develop_melody(
            theme,
            0.0,
            16.0,
            "piano",
            key_root="D",
            scale_type="minor",
            section_chords=_chords(),
            variation=0.0,
            rng=random.Random(1),
        )
        assert [n.pitch for n in out] == [n.pitch for n in theme]
        assert out[0].start_beat == 16.0

    def test_variation_develops_but_keeps_theme_recognizable(self) -> None:
        theme = _theme()
        out = develop_melody(
            theme,
            0.0,
            16.0,
            "piano",
            key_root="D",
            scale_type="minor",
            section_chords=_chords(),
            variation=0.4,
            rng=random.Random(3),
        )
        # Structure preserved: same count, rhythm, and phrase anchors.
        assert len(out) == len(theme)
        assert out[0].pitch == theme[0].pitch
        assert out[-1].pitch == theme[-1].pitch
        # Developed: at least one interior note differs, but most are kept.
        diffs = sum(1 for a, b in zip(theme, out, strict=True) if a.pitch != b.pitch)
        assert 0 < diffs < len(theme)

    def test_variation_is_deterministic_per_seed(self) -> None:
        theme = _theme()
        kw = dict(
            key_root="D",
            scale_type="minor",
            section_chords=_chords(),
            variation=0.4,
        )
        a = develop_melody(theme, 0.0, 16.0, "piano", rng=random.Random(9), **kw)
        b = develop_melody(theme, 0.0, 16.0, "piano", rng=random.Random(9), **kw)
        assert [n.pitch for n in a] == [n.pitch for n in b]


class TestGenreMelodicVariation:
    def test_leapy_genre_varies_more_than_conservative(self) -> None:
        ambient = get_genre_profile("ambient")
        jazz = get_genre_profile("jazz_bebop")
        assert genre_melodic_variation(jazz, 1) > genre_melodic_variation(ambient, 1)

    def test_variation_intensifies_with_each_return(self) -> None:
        jazz = get_genre_profile("jazz_bebop")
        assert genre_melodic_variation(jazz, 2) >= genre_melodic_variation(jazz, 1)

    def test_variation_is_bounded(self) -> None:
        jazz = get_genre_profile("jazz_bebop")
        assert 0.0 <= genre_melodic_variation(jazz, 5) <= 0.6


def _melody_pitches(genre: str) -> list[int]:
    spec = CompositionSpec(
        title="M",
        genre=genre,
        key="D minor",
        tempo_bpm=100.0,
        time_signature="4/4",
        instruments=[InstrumentSpec(name="piano", role="melody")],
        sections=[SectionSpec(name="A", bars=8, dynamics="mf")],
        generation=GenerationConfig(strategy="stochastic", seed=7, temperature=0.6),
    )
    score, _, _ = generate_via_v2_pipeline(spec)
    for section in score.sections:
        if section.name == "A":
            for part in section.parts:
                if part.instrument == "piano":
                    return [n.pitch for n in sorted(part.notes, key=lambda n: n.start_beat)]
    return []


def _avg_interval(pitches: list[int]) -> float:
    ivs = [abs(pitches[i + 1] - pitches[i]) for i in range(len(pitches) - 1)]
    return sum(ivs) / len(ivs) if ivs else 0.0


class TestGenreMelodicCharacter:
    def test_stepwise_genre_is_less_leapy_than_leapy_genre(self) -> None:
        ambient = _avg_interval(_melody_pitches("ambient"))
        classical = _avg_interval(_melody_pitches("classical_romantic"))
        assert ambient > 0 and classical > 0
        # Ambient should not out-leap a romantic-classical line.
        assert ambient <= classical

    def test_melody_stays_in_a_singable_register(self) -> None:
        # Register fold keeps the fill from marching to the ceiling.
        for genre in ("ambient", "jazz_bebop", "classical_romantic"):
            pitches = _melody_pitches(genre)
            assert pitches
            assert max(pitches) - min(pitches) <= 30, genre
