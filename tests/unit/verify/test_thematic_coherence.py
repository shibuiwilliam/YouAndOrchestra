"""Unit tests for thematic coherence analysis."""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.verify.thematic_coherence import analyze_thematic_coherence


def _make_score(
    section_pitches: list[list[int]],
    section_names: list[str] | None = None,
) -> ScoreIR:
    """Build a ScoreIR from per-section pitch sequences."""
    if section_names is None:
        section_names = [f"sec_{i}" for i in range(len(section_pitches))]

    sections = []
    bar = 0
    for name, pitches in zip(section_names, section_pitches, strict=False):
        notes = tuple(
            Note(pitch=p, start_beat=bar * 4.0 + i, duration_beats=1.0, velocity=80, instrument="piano")
            for i, p in enumerate(pitches)
        )
        n_bars = max(1, len(pitches) // 4 + 1)
        sections.append(
            Section(name=name, start_bar=bar, end_bar=bar + n_bars, parts=(Part(instrument="piano", notes=notes),))
        )
        bar += n_bars

    return ScoreIR(title="Test", tempo_bpm=120, time_signature="4/4", key="C major", sections=tuple(sections))


class TestThematicCoherence:
    """Test thematic coherence analysis."""

    def test_identical_sections_score_high(self) -> None:
        """Identical pitch sequences across sections → high coherence."""
        melody = [60, 62, 64, 65, 67, 65, 64, 62]
        score = _make_score([melody, melody, melody])
        report = analyze_thematic_coherence(score)
        assert report.section_correlation > 0.9
        assert report.first_last_similarity > 0.9
        assert report.overall_score > 0.8

    def test_unrelated_sections_score_lower(self) -> None:
        """Completely different pitch content → lower coherence."""
        score = _make_score(
            [
                [60, 62, 64, 65, 67, 69, 71, 72],  # C scale ascending
                [48, 51, 55, 58, 48, 51, 55, 58],  # Low arpeggios
                [84, 82, 80, 79, 77, 75, 74, 72],  # High descending
            ]
        )
        report = analyze_thematic_coherence(score)
        # Should be noticeably lower than identical sections
        assert report.overall_score < 0.9

    def test_single_section_returns_perfect(self) -> None:
        """A single section is trivially coherent."""
        score = _make_score([[60, 62, 64, 65]])
        report = analyze_thematic_coherence(score)
        assert report.overall_score == 1.0

    def test_first_last_similarity_detects_recall(self) -> None:
        """First and last sections sharing the same pitches → high similarity."""
        theme = [60, 64, 67, 72, 67, 64, 60, 60]
        contrast = [48, 51, 55, 58, 60, 55, 51, 48]
        score = _make_score([theme, contrast, theme])
        report = analyze_thematic_coherence(score)
        assert report.first_last_similarity > 0.9


class TestFeedbackActuators:
    """Test that feedback module handles theme-related findings."""

    def test_motif_recurrence_finding_triggers_recall(self) -> None:
        """A motif_recurrence finding should suggest theme recall."""
        from yao.conductor.feedback import _adaptation_for_finding
        from yao.schema.composition import (
            CompositionSpec,
            GenerationConfig,
            InstrumentSpec,
            SectionSpec,
        )
        from yao.verify.critique.types import Finding

        spec = CompositionSpec(
            title="Test",
            instruments=[InstrumentSpec(name="piano", role="melody")],
            sections=[
                SectionSpec(name="verse", bars=8, dynamics="mf"),
                SectionSpec(name="chorus", bars=8, dynamics="f"),
                SectionSpec(name="outro", bars=4, dynamics="mp"),
            ],
            generation=GenerationConfig(strategy="stochastic", temperature=0.5),
        )

        finding = Finding(
            rule_id="melody.motif_recurrence",
            severity="warning",
            role="melody",
            issue="Motif M1 only appears 1 time",
        )

        adaptation = _adaptation_for_finding(finding, spec, 0.5)
        assert adaptation is not None
        assert "recall_melody_from" in adaptation.field
        assert adaptation.new_value == "verse"
