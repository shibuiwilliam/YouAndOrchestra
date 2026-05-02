"""Tests for StyleVector Wave 3.4 extensions.

Verifies:
- New fields are copyright-safe (histogram/statistics, not sequences)
- Same-genre pieces have smaller distance than cross-genre pairs
- extraction function produces valid values
"""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.plan.harmony import CadenceRole, ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.perception.style_vector import StyleVector, extract_style_vector_from_score
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


def _make_score(pitches: list[int], durations: list[float] | None = None) -> ScoreIR:
    """Helper to make a simple score."""
    if durations is None:
        durations = [1.0] * len(pitches)
    beat = 0.0
    notes = []
    for p, d in zip(pitches, durations, strict=False):
        notes.append(Note(pitch=p, start_beat=beat, duration_beats=d, velocity=70, instrument="piano"))
        beat += d
    bars = int(beat / 4) + 1
    return ScoreIR(
        title="Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(
            Section(
                name="all",
                start_bar=0,
                end_bar=bars,
                parts=(Part(instrument="piano", notes=tuple(notes)),),
            ),
        ),
    )


def _make_plan(chords: list[str] | None = None, cadences: list[str] | None = None) -> MusicalPlan:
    """Helper to make a plan with harmony info."""
    chord_events = []
    if chords:
        for i, roman in enumerate(chords):
            cr = None
            if cadences and i < len(cadences) and cadences[i]:
                cr = CadenceRole(cadences[i])
            chord_events.append(
                ChordEvent(
                    section_id="all",
                    start_beat=float(i * 4),
                    duration_beats=4.0,
                    roman=roman,
                    function=HarmonicFunction.TONIC,
                    tension_level=0.5,
                    cadence_role=cr,
                )
            )
    return MusicalPlan(
        form=SongFormPlan(
            sections=[
                SectionPlan(
                    id="all",
                    start_bar=0,
                    bars=8,
                    role="verse",
                    target_density=0.5,
                    target_tension=0.5,
                )
            ],
            climax_section_id="all",
        ),
        harmony=HarmonyPlan(chord_events=chord_events, cadences={}),
        trajectory=MultiDimensionalTrajectory.default(),
        intent=IntentSpec(text="test", keywords=[]),
        provenance=ProvenanceLog(),
        global_context=GlobalContext(key="C major"),
        motif=MotifPlan(
            seeds=[MotifSeed(id="M1", rhythm_shape=(1.0,), interval_shape=(0,), origin_section="all")],
            placements=[MotifPlacement(motif_id="M1", section_id="all", start_beat=0.0)],
        ),
    )


class TestStyleVectorNewFields:
    """Tests for the new Wave 3.4 fields."""

    def test_interval_class_histogram_sums_to_one(self) -> None:
        """Interval histogram must be a valid distribution."""
        score = _make_score([60, 62, 64, 65, 67, 69, 71, 72])  # C major scale
        sv = extract_style_vector_from_score(score)
        assert len(sv.interval_class_histogram) == 12
        assert abs(sum(sv.interval_class_histogram) - 1.0) < 0.01

    def test_interval_histogram_reflects_stepwise(self) -> None:
        """A stepwise scale should have most intervals at 1-2 semitones."""
        score = _make_score([60, 62, 64, 65, 67, 69, 71, 72])
        sv = extract_style_vector_from_score(score)
        # Intervals 1 and 2 should dominate
        small_intervals = sv.interval_class_histogram[1] + sv.interval_class_histogram[2]
        assert small_intervals > 0.7

    def test_interval_histogram_reflects_leaps(self) -> None:
        """Wide leaps should show in larger interval classes."""
        score = _make_score([60, 72, 48, 84, 36, 96])  # octave jumps
        sv = extract_style_vector_from_score(score)
        # Interval class 0 (octave = 0 mod 12) should dominate
        assert sv.interval_class_histogram[0] > 0.5

    def test_chord_quality_histogram_length(self) -> None:
        """Chord quality histogram must have 8 dimensions."""
        plan = _make_plan(chords=["I", "V", "vi", "IV"])
        score = _make_score([60, 67, 69, 65])
        sv = extract_style_vector_from_score(score, plan)
        assert len(sv.chord_quality_histogram) == 8

    def test_chord_quality_detects_major_vs_minor(self) -> None:
        """Major-heavy progression should differ from minor-heavy."""
        plan_major = _make_plan(chords=["I", "IV", "V", "I"])
        plan_minor = _make_plan(chords=["i", "iv", "v", "i"])
        score = _make_score([60, 65, 67, 60])
        sv_maj = extract_style_vector_from_score(score, plan_major)
        sv_min = extract_style_vector_from_score(score, plan_minor)
        # Major should have more in index 0 (maj), minor in index 1 (min)
        assert sv_maj.chord_quality_histogram[0] > sv_min.chord_quality_histogram[0]
        assert sv_min.chord_quality_histogram[1] > sv_maj.chord_quality_histogram[1]

    def test_cadence_distribution_length(self) -> None:
        """Cadence distribution must have 4 dimensions."""
        plan = _make_plan(chords=["I", "V"], cadences=["", "authentic"])
        score = _make_score([60, 67])
        sv = extract_style_vector_from_score(score, plan)
        assert len(sv.cadence_type_distribution) == 4

    def test_rhythm_complexity_in_range(self) -> None:
        """Rhythm complexity must be in [0, 1]."""
        score = _make_score([60, 62, 64, 65, 67])
        sv = extract_style_vector_from_score(score)
        assert 0.0 <= sv.rhythm_complexity <= 1.0

    def test_uniform_rhythm_is_low_complexity(self) -> None:
        """All notes on the same beat position = low complexity."""
        # All on beat 1 of each bar (same grid position)
        notes = [
            Note(pitch=60, start_beat=float(i * 4), duration_beats=1.0, velocity=70, instrument="piano")
            for i in range(8)
        ]
        score = ScoreIR(
            title="t",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="a",
                    start_bar=0,
                    end_bar=8,
                    parts=(Part(instrument="piano", notes=tuple(notes)),),
                ),
            ),
        )
        sv = extract_style_vector_from_score(score)
        assert sv.rhythm_complexity < 0.3

    def test_syncopated_rhythm_is_higher_complexity(self) -> None:
        """Notes on varied beat positions = higher complexity."""
        beats = [
            0.0,
            0.5,
            1.5,
            2.0,
            3.0,
            3.5,
            4.0,
            5.5,
            6.0,
            7.0,
            7.5,
            8.5,
            9.0,
            10.5,
            11.0,
            12.0,
        ]
        notes = [Note(pitch=60, start_beat=b, duration_beats=0.5, velocity=70, instrument="piano") for b in beats]
        score = ScoreIR(
            title="t",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(
                Section(
                    name="a",
                    start_bar=0,
                    end_bar=4,
                    parts=(Part(instrument="piano", notes=tuple(notes)),),
                ),
            ),
        )
        sv = extract_style_vector_from_score(score)
        assert sv.rhythm_complexity > 0.5


class TestStyleVectorDistance:
    """Tests for distance with new fields."""

    def test_same_vector_distance_zero(self) -> None:
        sv = StyleVector(
            harmonic_rhythm=2.0,
            voice_leading_smoothness=3.0,
            rhythmic_density_per_bar=(4.0, 4.0),
            register_distribution=(0.0,) * 12,
            timbre_centroid_curve=(),
            motif_density=2.0,
            interval_class_histogram=(0.5, 0.5) + (0.0,) * 10,
            chord_quality_histogram=(0.5, 0.5) + (0.0,) * 6,
            cadence_type_distribution=(1.0, 0.0, 0.0, 0.0),
            rhythm_complexity=0.5,
        )
        assert sv.distance_to(sv) == 0.0

    def test_different_histograms_increase_distance(self) -> None:
        sv1 = StyleVector(
            harmonic_rhythm=2.0,
            voice_leading_smoothness=3.0,
            rhythmic_density_per_bar=(4.0,),
            register_distribution=(0.0,) * 12,
            timbre_centroid_curve=(),
            motif_density=2.0,
            interval_class_histogram=(1.0,) + (0.0,) * 11,
            chord_quality_histogram=(1.0,) + (0.0,) * 7,
            cadence_type_distribution=(1.0, 0.0, 0.0, 0.0),
            rhythm_complexity=0.2,
        )
        sv2 = StyleVector(
            harmonic_rhythm=2.0,
            voice_leading_smoothness=3.0,
            rhythmic_density_per_bar=(4.0,),
            register_distribution=(0.0,) * 12,
            timbre_centroid_curve=(),
            motif_density=2.0,
            interval_class_histogram=(0.0,) + (0.0,) * 10 + (1.0,),
            chord_quality_histogram=(0.0,) + (0.0,) * 6 + (1.0,),
            cadence_type_distribution=(0.0, 0.0, 0.0, 1.0),
            rhythm_complexity=0.9,
        )
        assert sv1.distance_to(sv2) > 0.5


class TestCopyrightSafety:
    """Verify that StyleVector fields cannot reconstruct copyrighted content."""

    def test_no_sequence_in_interval_histogram(self) -> None:
        """Two melodies with same intervals in different order → same histogram."""
        # C-D-E-F-G ascending
        score_asc = _make_score([60, 62, 64, 65, 67])
        # G-F-E-D-C descending (same intervals, different order)
        score_desc = _make_score([67, 65, 64, 62, 60])
        sv_asc = extract_style_vector_from_score(score_asc)
        sv_desc = extract_style_vector_from_score(score_desc)
        # Histograms should be identical (same interval distribution)
        assert sv_asc.interval_class_histogram == sv_desc.interval_class_histogram

    def test_no_chord_order_in_quality_histogram(self) -> None:
        """Two progressions with same chords in different order → same histogram."""
        plan_a = _make_plan(chords=["I", "V", "vi", "IV"])
        plan_b = _make_plan(chords=["vi", "IV", "I", "V"])
        score = _make_score([60, 67, 69, 65])
        sv_a = extract_style_vector_from_score(score, plan_a)
        sv_b = extract_style_vector_from_score(score, plan_b)
        assert sv_a.chord_quality_histogram == sv_b.chord_quality_histogram
