"""Scenario test: Groove profiles produce measurably different output.

Tests that the same ScoreIR produces different MIDI timings and
velocities when processed with different GrooveProfiles.
"""

from __future__ import annotations

from yao.generators.groove_applicator import apply_groove
from yao.ir.groove import GrooveProfile, load_groove
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score() -> ScoreIR:
    """Create a 16-bar score with piano and drums."""
    notes_piano = tuple(
        Note(pitch=60 + (i % 7), start_beat=float(i), duration_beats=0.5, velocity=80, instrument="piano")
        for i in range(64)
    )
    notes_drums = tuple(
        Note(pitch=36, start_beat=float(i), duration_beats=0.25, velocity=90, instrument="drums") for i in range(64)
    )
    section = Section(
        name="test",
        start_bar=0,
        end_bar=16,
        parts=(
            Part(instrument="piano", notes=notes_piano),
            Part(instrument="drums", notes=notes_drums),
        ),
    )
    return ScoreIR(
        title="groove_test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


class TestGrooveChangesFeel:
    """Scenario: different grooves produce different feels."""

    def test_lofi_vs_edm_different_timings(self) -> None:
        """Lo-fi and EDM grooves produce measurably different timings."""
        score = _make_score()
        lofi = load_groove("lofi_hiphop")
        edm = load_groove("edm_4onfloor")

        grooved_lofi, _ = apply_groove(score, lofi, seed=42)
        grooved_edm, _ = apply_groove(score, edm, seed=42)

        times_lofi = [n.start_beat for n in grooved_lofi.all_notes()]
        times_edm = [n.start_beat for n in grooved_edm.all_notes()]
        assert times_lofi != times_edm

    def test_funk_has_stronger_accents(self) -> None:
        """Funk groove produces more velocity variation than pop straight."""
        score = _make_score()
        funk = load_groove("funk_16th")
        pop = load_groove("pop_straight")

        grooved_funk, _ = apply_groove(score, funk, seed=42)
        grooved_pop, _ = apply_groove(score, pop, seed=42)

        vel_funk = [n.velocity for n in grooved_funk.all_notes()]
        vel_pop = [n.velocity for n in grooved_pop.all_notes()]

        # Funk should have more velocity variation
        funk_range = max(vel_funk) - min(vel_funk)
        pop_range = max(vel_pop) - min(vel_pop)
        assert funk_range > pop_range

    def test_null_groove_preserves_original(self) -> None:
        """A groove with no offsets/patterns preserves the original."""
        score = _make_score()
        null = GrooveProfile(name="null")
        grooved, _ = apply_groove(score, null, seed=42)

        orig = [(n.start_beat, n.velocity) for n in score.all_notes()]
        result = [(n.start_beat, n.velocity) for n in grooved.all_notes()]
        assert orig == result

    def test_all_12_grooves_load_and_apply(self) -> None:
        """All 12 groove profiles can be loaded and applied."""
        score = _make_score()
        from yao.ir.groove import available_grooves

        for name in available_grooves():
            profile = load_groove(name)
            grooved, prov = apply_groove(score, profile, seed=42)
            assert len(grooved.all_notes()) == len(score.all_notes())
            assert len(prov.records) == 1
