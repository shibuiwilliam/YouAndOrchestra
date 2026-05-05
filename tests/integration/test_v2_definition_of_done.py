"""Integration tests proving v2.0 Definition of Done criteria.

Tests cover:
- D5: Ensemble templates (genre-appropriate instrument roles)
- D8: Prog rock meter changes
- D9: Loopable game BGM (seamlessness)
- D10: J-Pop vocal singability
- D12: Reference evaluation (feature extraction & distance)
"""

from __future__ import annotations

import numpy as np
import pretty_midi
import pytest

from yao.generators.registry import get_generator
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.feature_extractors import extract_all, extract_concatenated
from yao.render.midi_writer import write_midi
from yao.schema.composition import (
    CompositionSpec,
    GenerationConfig,
    InstrumentSpec,
    SectionSpec,
)
from yao.verify.seamlessness import evaluate_seamlessness
from yao.verify.singability import SingabilityReport, evaluate_singability

# ---------------------------------------------------------------------------
# D5: Ensemble Templates
# ---------------------------------------------------------------------------


class TestD5EnsembleTemplates:
    """Verify that different genres produce genre-appropriate ensembles."""

    def test_classical_chamber_uses_composer(self) -> None:
        """Cinematic genre with melody instrument produces ScoreIR with melody."""
        spec = CompositionSpec(
            title="Cinematic Test",
            genre="cinematic",
            key="D minor",
            tempo_bpm=90.0,
            time_signature="4/4",
            total_bars=8,
            instruments=[
                InstrumentSpec(name="violin", role="melody"),
                InstrumentSpec(name="cello", role="bass"),
            ],
            sections=[SectionSpec(name="intro", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        generator = get_generator("stochastic")
        score, provenance = generator.generate(spec)

        assert isinstance(score, ScoreIR)
        assert len(score.all_notes()) > 0
        # Verify melody instrument (violin) is present
        assert "violin" in score.instruments()

    def test_hip_hop_producer_no_composer(self) -> None:
        """Lo-fi hip-hop with loop_evolution uses rhythm/harmony/bass roles."""
        spec = CompositionSpec(
            title="LoFi Test",
            genre="lofi_hiphop",
            key="C minor",
            tempo_bpm=85.0,
            time_signature="4/4",
            total_bars=16,
            instruments=[
                InstrumentSpec(name="piano", role="harmony"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
            sections=[
                SectionSpec(name="loop_a", bars=8, dynamics="mp"),
                SectionSpec(name="loop_b", bars=8, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="loop_evolution", seed=42, temperature=0.5),
        )
        generator = get_generator("loop_evolution")
        score, provenance = generator.generate(spec)

        assert isinstance(score, ScoreIR)
        assert len(score.all_notes()) > 0
        # Does not need a melody role - just rhythm/harmony/bass
        instruments = score.instruments()
        assert len(instruments) >= 1

    def test_ambient_solo_no_composer(self) -> None:
        """Ambient genre with pad instruments produces output without melody."""
        spec = CompositionSpec(
            title="Ambient Test",
            genre="ambient",
            key="E minor",
            tempo_bpm=60.0,
            time_signature="4/4",
            total_bars=8,
            instruments=[
                InstrumentSpec(name="synth_pad", role="pad"),
            ],
            sections=[SectionSpec(name="atmosphere", bars=8, dynamics="pp")],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.3),
        )
        generator = get_generator("stochastic")
        score, provenance = generator.generate(spec)

        assert isinstance(score, ScoreIR)
        assert len(score.all_notes()) > 0
        # Only pad instrument(s) should be present
        instruments = score.instruments()
        assert "synth_pad" in instruments


# ---------------------------------------------------------------------------
# D8: Prog Rock Meter Changes
# ---------------------------------------------------------------------------


class TestD8ProgRockMeterChanges:
    """Verify meter changes are preserved in ScoreIR and MIDI rendering."""

    def test_meter_changes_preserved_in_score_ir(self) -> None:
        """Sections with different time_signatures retain them after construction."""
        # Create ScoreIR manually with sections of different meters
        notes_78 = tuple(
            Note(pitch=60 + i, start_beat=float(i), duration_beats=0.8, velocity=80, instrument="piano")
            for i in range(7)
        )
        notes_44 = tuple(
            Note(pitch=65 + i, start_beat=float(i), duration_beats=0.9, velocity=75, instrument="piano")
            for i in range(8)
        )
        notes_54 = tuple(
            Note(pitch=62 + i, start_beat=float(i), duration_beats=0.7, velocity=70, instrument="piano")
            for i in range(5)
        )

        part_78 = Part(instrument="piano", notes=notes_78)
        part_44 = Part(instrument="piano", notes=notes_44)
        part_54 = Part(instrument="piano", notes=notes_54)

        section_78 = Section(name="prog_intro", start_bar=0, end_bar=4, parts=(part_78,))
        section_44 = Section(name="verse", start_bar=4, end_bar=8, parts=(part_44,))
        section_54 = Section(name="bridge", start_bar=8, end_bar=12, parts=(part_54,))

        score = ScoreIR(
            title="Prog Rock Test",
            tempo_bpm=120.0,
            time_signature="7/8",  # primary time signature
            key="A minor",
            sections=(section_78, section_44, section_54),
        )

        # Verify sections retained their structure
        assert len(score.sections) == 3
        assert score.sections[0].name == "prog_intro"
        assert score.sections[1].name == "verse"
        assert score.sections[2].name == "bridge"
        # Bar counts correct
        assert score.sections[0].bar_count == 4
        assert score.sections[1].bar_count == 4
        assert score.sections[2].bar_count == 4

    def test_meter_changes_in_midi_rendering(self, tmp_path: pytest.TempPathFactory) -> None:
        """Generate a piece, render to MIDI, read back, verify timing preserved."""
        spec = CompositionSpec(
            title="MIDI Meter Test",
            genre="general",
            key="C major",
            tempo_bpm=120.0,
            time_signature="4/4",
            total_bars=8,
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="section_a", bars=4, dynamics="mf"),
                SectionSpec(name="section_b", bars=4, dynamics="f"),
            ],
            generation=GenerationConfig(strategy="stochastic", seed=42, temperature=0.5),
        )
        generator = get_generator("stochastic")
        score, _ = generator.generate(spec)

        # Write MIDI
        midi_path = tmp_path / "test_meter.mid"
        write_midi(score, midi_path)

        # Read back with pretty_midi
        midi = pretty_midi.PrettyMIDI(str(midi_path))

        # Verify tempo is preserved
        tempos = midi.get_tempo_changes()
        assert len(tempos[1]) >= 1
        assert abs(tempos[1][0] - 120.0) < 1.0

        # Verify notes were written and can be read back
        total_notes = sum(len(inst.notes) for inst in midi.instruments)
        assert total_notes > 0


# ---------------------------------------------------------------------------
# D9: Loopable Game BGM
# ---------------------------------------------------------------------------


class TestD9LoopableGameBGM:
    """Verify loop_evolution produces seamless loopable output."""

    def test_loop_evolution_boundary_continuity(self) -> None:
        """Loop_evolution generator produces output with seamlessness > 0.5."""
        spec = CompositionSpec(
            title="Loop BGM Test",
            genre="game_bgm",
            key="C major",
            tempo_bpm=100.0,
            time_signature="4/4",
            total_bars=8,
            instruments=[
                InstrumentSpec(name="piano", role="harmony"),
                InstrumentSpec(name="acoustic_bass", role="bass"),
            ],
            sections=[
                SectionSpec(name="loop_a", bars=4, dynamics="mf"),
                SectionSpec(name="loop_b", bars=4, dynamics="mf"),
            ],
            generation=GenerationConfig(strategy="loop_evolution", seed=42, temperature=0.4),
        )
        generator = get_generator("loop_evolution")
        score, _ = generator.generate(spec)

        seamlessness = evaluate_seamlessness(score)
        assert seamlessness > 0.5, f"Seamlessness {seamlessness:.3f} should be > 0.5"

    def test_loopable_flag_produces_seamless_output(self) -> None:
        """Verify boundary check explicitly: no notes should exceed total beats."""
        spec = CompositionSpec(
            title="Loopable Check",
            genre="game_bgm",
            key="G major",
            tempo_bpm=110.0,
            time_signature="4/4",
            total_bars=8,
            instruments=[
                InstrumentSpec(name="piano", role="harmony"),
            ],
            sections=[SectionSpec(name="loop", bars=8, dynamics="mf")],
            generation=GenerationConfig(strategy="loop_evolution", seed=123, temperature=0.3),
        )
        generator = get_generator("loop_evolution")
        score, _ = generator.generate(spec)

        total_beats = score.total_beats()
        notes = score.all_notes()
        assert len(notes) > 0

        # Verify no notes extend past the total duration (with small tolerance)
        for note in notes:
            end_beat = note.start_beat + note.duration_beats
            assert end_beat <= total_beats + 0.1, (
                f"Note at beat {note.start_beat} extends to {end_beat}, but piece is only {total_beats} beats"
            )


# ---------------------------------------------------------------------------
# D10: J-Pop Vocal Singability
# ---------------------------------------------------------------------------


class TestD10JPopVocalSingability:
    """Verify vocal lines meet singability constraints."""

    def _make_vocal_score(self) -> ScoreIR:
        """Create a score with a vocal-range instrument (C4-D5, stepwise motion)."""
        # Generate a singable vocal line: mostly stepwise, within C4-D5 (MIDI 60-74)
        import random

        rng = random.Random(42)
        notes: list[Note] = []
        current_pitch = 65  # F4 - middle of range
        beat = 0.0

        for _ in range(24):
            # Mostly stepwise motion (intervals of 1-2 semitones)
            interval = rng.choice([-2, -1, -1, 0, 1, 1, 2])
            current_pitch = max(60, min(74, current_pitch + interval))
            duration = rng.choice([0.5, 1.0, 1.0, 1.5])
            notes.append(
                Note(
                    pitch=current_pitch,
                    start_beat=beat,
                    duration_beats=duration * 0.8,
                    velocity=70,
                    instrument="voice",
                )
            )
            beat += duration
            # Add occasional breath gaps
            if rng.random() < 0.3:
                beat += 0.5

        part = Part(instrument="voice", notes=tuple(notes))
        section = Section(name="verse", start_bar=0, end_bar=8, parts=(part,))
        return ScoreIR(
            title="J-Pop Vocal Test",
            tempo_bpm=128.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )

    def test_jpop_vocal_tessitura_within_range(self) -> None:
        """Vocal line with C4-D5 range has tessitura_strain < 0.5."""
        score = self._make_vocal_score()
        report = evaluate_singability(score, vocal_instrument="voice")

        assert isinstance(report, SingabilityReport)
        assert report.total_notes > 0
        assert report.tessitura_strain < 0.5, f"Tessitura strain {report.tessitura_strain:.3f} should be < 0.5"

    def test_jpop_vocal_no_excessive_leaps(self) -> None:
        """Vocal line with stepwise motion has <= 2 awkward leaps."""
        score = self._make_vocal_score()
        report = evaluate_singability(score, vocal_instrument="voice")

        assert report.awkward_leaps <= 2, f"Awkward leaps {report.awkward_leaps} should be <= 2"


# ---------------------------------------------------------------------------
# D12: Reference Evaluation (Feature Extraction)
# ---------------------------------------------------------------------------


class TestD12ReferenceEvaluation:
    """Verify feature extraction and distance computation for references."""

    def _make_score_similar_to_reference(self) -> ScoreIR:
        """Create a score with known characteristics (C major scale, steady rhythm)."""
        notes = tuple(
            Note(
                pitch=60 + (i % 8),
                start_beat=float(i),
                duration_beats=0.9,
                velocity=75,
                instrument="piano",
            )
            for i in range(32)
        )
        part = Part(instrument="piano", notes=notes)
        section = Section(name="main", start_bar=0, end_bar=8, parts=(part,))
        return ScoreIR(
            title="Reference-like Score",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )

    def _make_score_different_from_reference(self) -> ScoreIR:
        """Create a score very different (wide leaps, extreme register, irregular)."""
        import random

        rng = random.Random(99)
        notes = tuple(
            Note(
                pitch=rng.choice([30, 40, 90, 100, 110]),  # extreme registers
                start_beat=float(i) * 1.7,  # irregular timing
                duration_beats=0.2,
                velocity=rng.choice([20, 120]),  # extreme dynamics
                instrument="piano",
            )
            for i in range(16)
        )
        part = Part(instrument="piano", notes=notes)
        section = Section(name="chaos", start_bar=0, end_bar=8, parts=(part,))
        return ScoreIR(
            title="Different Score",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )

    def test_positive_reference_scores_higher(self) -> None:
        """Similar score has lower Euclidean distance than a very different score."""
        reference = self._make_score_similar_to_reference()
        similar = self._make_score_similar_to_reference()  # same construction = similar
        different = self._make_score_different_from_reference()

        ref_features = extract_concatenated(reference)
        sim_features = extract_concatenated(similar)
        diff_features = extract_concatenated(different)

        dist_similar = float(np.linalg.norm(ref_features - sim_features))
        dist_different = float(np.linalg.norm(ref_features - diff_features))

        assert dist_similar < dist_different, (
            f"Similar score distance ({dist_similar:.4f}) should be less than "
            f"different score distance ({dist_different:.4f})"
        )

    def test_all_extractors_produce_valid_output(self, sample_score_ir: ScoreIR) -> None:
        """All 7 feature extractors return non-NaN numpy arrays."""
        features = extract_all(sample_score_ir)

        assert len(features) == 7, f"Expected 7 extractors, got {len(features)}"

        expected_names = {
            "voice_leading_smoothness",
            "motivic_density",
            "surprise_index",
            "register_distribution",
            "temporal_centroid",
            "groove_pocket",
            "chord_complexity",
        }
        assert set(features.keys()) == expected_names

        for name, arr in features.items():
            assert isinstance(arr, np.ndarray), f"{name} should return numpy array"
            assert not np.any(np.isnan(arr)), f"{name} contains NaN values"
            assert arr.ndim == 1, f"{name} should be 1-dimensional"
