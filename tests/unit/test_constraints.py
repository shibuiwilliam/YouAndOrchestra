"""Tests for the constraint system."""

from __future__ import annotations

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.schema.constraints import Constraint, ConstraintsSpec
from yao.verify.constraint_checker import check_constraints


def _make_score_with_notes(notes: tuple[Note, ...]) -> ScoreIR:
    """Create a score from a tuple of notes."""
    part = Part(instrument="piano", notes=notes)
    section = Section(name="verse", start_bar=0, end_bar=4, parts=(part,))
    return ScoreIR(
        title="Constraint Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


class TestConstraintSchema:
    def test_create_constraint(self) -> None:
        c = Constraint(type="must_not", rule="no_parallel_fifths")
        assert c.type == "must_not"
        assert c.scope == "global"
        assert c.severity == "warning"

    def test_constraints_spec(self) -> None:
        spec = ConstraintsSpec(
            constraints=[
                Constraint(type="must_not", rule="no_parallel_fifths"),
                Constraint(type="avoid", rule="note_above:C6", scope="instrument:piano"),
            ]
        )
        assert len(spec.constraints) == 2


class TestMaxDensity:
    def test_detects_high_density(self) -> None:
        # 5 notes at the same beat
        notes = tuple(
            Note(pitch=60 + i, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
            for i in range(5)
        )
        score = _make_score_with_notes(notes)
        constraints = ConstraintsSpec(
            constraints=[
                Constraint(type="must_not", rule="max_density:3", severity="error"),
            ]
        )
        results = check_constraints(score, constraints)
        assert len(results) > 0
        assert results[0].rule == "constraint:max_density"

    def test_passes_low_density(self) -> None:
        notes = tuple(
            Note(
                pitch=60 + i,
                start_beat=float(i),
                duration_beats=1.0,
                velocity=80,
                instrument="piano",
            )
            for i in range(4)
        )
        score = _make_score_with_notes(notes)
        constraints = ConstraintsSpec(
            constraints=[
                Constraint(type="must_not", rule="max_density:3"),
            ]
        )
        results = check_constraints(score, constraints)
        assert len(results) == 0


class TestNoteLimits:
    def test_detects_note_above_limit(self) -> None:
        notes = (
            Note(pitch=84, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
        )
        score = _make_score_with_notes(notes)
        constraints = ConstraintsSpec(
            constraints=[
                Constraint(type="must_not", rule="note_above:C5"),
            ]
        )
        results = check_constraints(score, constraints)
        assert len(results) == 1
        assert "note_above" in results[0].rule

    def test_passes_within_limit(self) -> None:
        notes = (
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
        )
        score = _make_score_with_notes(notes)
        constraints = ConstraintsSpec(
            constraints=[
                Constraint(type="must_not", rule="note_above:C6"),
            ]
        )
        results = check_constraints(score, constraints)
        assert len(results) == 0


class TestScopedConstraints:
    def test_section_scope(self) -> None:
        notes_verse = (
            Note(pitch=84, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
        )
        notes_chorus = (
            Note(pitch=84, start_beat=16.0, duration_beats=1.0, velocity=80, instrument="piano"),
        )
        part_v = Part(instrument="piano", notes=notes_verse)
        part_c = Part(instrument="piano", notes=notes_chorus)
        sec_v = Section(name="verse", start_bar=0, end_bar=4, parts=(part_v,))
        sec_c = Section(name="chorus", start_bar=4, end_bar=8, parts=(part_c,))
        score = ScoreIR(
            title="Scope Test",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(sec_v, sec_c),
        )
        # Only constrain the verse section
        constraints = ConstraintsSpec(
            constraints=[
                Constraint(type="must_not", rule="note_above:C5", scope="section:verse"),
            ]
        )
        results = check_constraints(score, constraints)
        assert len(results) == 1  # Only the verse note should violate


class TestEmptyConstraints:
    def test_no_constraints_no_results(self) -> None:
        notes = (
            Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano"),
        )
        score = _make_score_with_notes(notes)
        constraints = ConstraintsSpec(constraints=[])
        results = check_constraints(score, constraints)
        assert len(results) == 0
