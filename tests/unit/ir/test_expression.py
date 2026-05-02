"""Unit tests for the Performance Expression IR (Layer 4.5)."""

from __future__ import annotations

import pytest

from yao.errors import ExpressionValidationError
from yao.ir.expression import (
    BreathMark,
    NoteExpression,
    NoteId,
    PedalCurve,
    PerformanceLayer,
    RubatoCurve,
)

# ---------------------------------------------------------------------------
# Frozen immutability
# ---------------------------------------------------------------------------


class TestFrozen:
    def test_note_expression_is_frozen(self) -> None:
        expr = NoteExpression()
        with pytest.raises(AttributeError):
            expr.legato_overlap = 0.5  # type: ignore[misc]

    def test_rubato_curve_is_frozen(self) -> None:
        rc = RubatoCurve(section_name="verse", waypoints=((0.0, 1.0),))
        with pytest.raises(AttributeError):
            rc.section_name = "chorus"  # type: ignore[misc]

    def test_breath_mark_is_frozen(self) -> None:
        bm = BreathMark(beat_position=4.0, duration_beats=0.5)
        with pytest.raises(AttributeError):
            bm.beat_position = 8.0  # type: ignore[misc]

    def test_pedal_curve_is_frozen(self) -> None:
        pc = PedalCurve(cc_number=64, instrument="piano", events=((0.0, 127),))
        with pytest.raises(AttributeError):
            pc.cc_number = 11  # type: ignore[misc]

    def test_performance_layer_is_frozen(self) -> None:
        pl = PerformanceLayer.empty()
        with pytest.raises(AttributeError):
            pl.breath_marks = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# NoteExpression defaults and creation
# ---------------------------------------------------------------------------


class TestNoteExpressionDefaults:
    def test_default_values(self) -> None:
        expr = NoteExpression()
        assert expr.legato_overlap == 0.0
        assert expr.accent_strength == 0.0
        assert expr.glissando_to is None
        assert expr.pitch_bend_curve is None
        assert expr.cc_curves is None
        assert expr.micro_timing_ms == 0.0
        assert expr.micro_dynamics == 0.0

    def test_custom_values(self) -> None:
        expr = NoteExpression(
            legato_overlap=0.05,
            accent_strength=0.8,
            glissando_to=67,
            pitch_bend_curve=((0.0, 0), (0.5, 4096)),
            cc_curves={1: ((0.0, 64), (1.0, 127))},
            micro_timing_ms=-5.0,
            micro_dynamics=0.2,
        )
        assert expr.legato_overlap == 0.05
        assert expr.accent_strength == 0.8
        assert expr.glissando_to == 67
        assert expr.pitch_bend_curve == ((0.0, 0), (0.5, 4096))
        assert expr.cc_curves == {1: ((0.0, 64), (1.0, 127))}
        assert expr.micro_timing_ms == -5.0
        assert expr.micro_dynamics == 0.2

    def test_default_validates_ok(self) -> None:
        NoteExpression().validate()


# ---------------------------------------------------------------------------
# NoteExpression validation
# ---------------------------------------------------------------------------


class TestNoteExpressionValidation:
    def test_accent_too_high(self) -> None:
        expr = NoteExpression(accent_strength=1.5)
        with pytest.raises(ExpressionValidationError, match="accent_strength"):
            expr.validate()

    def test_accent_negative(self) -> None:
        expr = NoteExpression(accent_strength=-0.1)
        with pytest.raises(ExpressionValidationError, match="accent_strength"):
            expr.validate()

    def test_accent_at_bounds(self) -> None:
        NoteExpression(accent_strength=0.0).validate()
        NoteExpression(accent_strength=1.0).validate()

    def test_micro_dynamics_too_high(self) -> None:
        expr = NoteExpression(micro_dynamics=1.5)
        with pytest.raises(ExpressionValidationError, match="micro_dynamics"):
            expr.validate()

    def test_micro_dynamics_too_low(self) -> None:
        expr = NoteExpression(micro_dynamics=-1.5)
        with pytest.raises(ExpressionValidationError, match="micro_dynamics"):
            expr.validate()

    def test_glissando_out_of_range(self) -> None:
        expr = NoteExpression(glissando_to=128)
        with pytest.raises(ExpressionValidationError, match="glissando_to"):
            expr.validate()

    def test_glissando_negative(self) -> None:
        expr = NoteExpression(glissando_to=-1)
        with pytest.raises(ExpressionValidationError, match="glissando_to"):
            expr.validate()

    def test_glissando_valid_bounds(self) -> None:
        NoteExpression(glissando_to=0).validate()
        NoteExpression(glissando_to=127).validate()

    def test_pitch_bend_too_high(self) -> None:
        expr = NoteExpression(pitch_bend_curve=((0.0, 8192),))
        with pytest.raises(ExpressionValidationError, match="Pitch bend"):
            expr.validate()

    def test_pitch_bend_too_low(self) -> None:
        expr = NoteExpression(pitch_bend_curve=((0.0, -8193),))
        with pytest.raises(ExpressionValidationError, match="Pitch bend"):
            expr.validate()

    def test_pitch_bend_valid_bounds(self) -> None:
        NoteExpression(pitch_bend_curve=((0.0, -8192), (1.0, 8191))).validate()

    def test_cc_value_too_high(self) -> None:
        expr = NoteExpression(cc_curves={1: ((0.0, 128),)})
        with pytest.raises(ExpressionValidationError, match="CC value"):
            expr.validate()

    def test_cc_value_negative(self) -> None:
        expr = NoteExpression(cc_curves={1: ((0.0, -1),)})
        with pytest.raises(ExpressionValidationError, match="CC value"):
            expr.validate()

    def test_cc_number_out_of_range(self) -> None:
        expr = NoteExpression(cc_curves={128: ((0.0, 64),)})
        with pytest.raises(ExpressionValidationError, match="CC number"):
            expr.validate()

    def test_cc_valid_bounds(self) -> None:
        NoteExpression(cc_curves={0: ((0.0, 0),), 127: ((0.0, 127),)}).validate()


# ---------------------------------------------------------------------------
# RubatoCurve validation
# ---------------------------------------------------------------------------


class TestRubatoCurve:
    def test_valid(self) -> None:
        rc = RubatoCurve(section_name="verse", waypoints=((0.0, 0.9), (4.0, 1.1)))
        rc.validate()

    def test_invalid_zero_ratio(self) -> None:
        rc = RubatoCurve(section_name="verse", waypoints=((0.0, 0.0),))
        with pytest.raises(ExpressionValidationError, match="tempo_ratio"):
            rc.validate()

    def test_invalid_negative_ratio(self) -> None:
        rc = RubatoCurve(section_name="verse", waypoints=((0.0, -0.5),))
        with pytest.raises(ExpressionValidationError, match="tempo_ratio"):
            rc.validate()


# ---------------------------------------------------------------------------
# BreathMark validation
# ---------------------------------------------------------------------------


class TestBreathMark:
    def test_valid_global(self) -> None:
        bm = BreathMark(beat_position=8.0, duration_beats=0.25)
        bm.validate()
        assert bm.instrument is None

    def test_valid_instrument_specific(self) -> None:
        bm = BreathMark(beat_position=8.0, duration_beats=0.5, instrument="violin")
        bm.validate()
        assert bm.instrument == "violin"

    def test_invalid_negative_duration(self) -> None:
        bm = BreathMark(beat_position=0.0, duration_beats=-0.1)
        with pytest.raises(ExpressionValidationError, match="duration"):
            bm.validate()

    def test_zero_duration_ok(self) -> None:
        BreathMark(beat_position=0.0, duration_beats=0.0).validate()


# ---------------------------------------------------------------------------
# PedalCurve validation
# ---------------------------------------------------------------------------


class TestPedalCurve:
    def test_valid_sustain(self) -> None:
        pc = PedalCurve(
            cc_number=64,
            instrument="piano",
            events=((0.0, 127), (4.0, 0)),
        )
        pc.validate()

    def test_invalid_cc_number(self) -> None:
        pc = PedalCurve(cc_number=128, instrument="piano", events=())
        with pytest.raises(ExpressionValidationError, match="cc_number"):
            pc.validate()

    def test_invalid_event_value(self) -> None:
        pc = PedalCurve(cc_number=64, instrument="piano", events=((0.0, 200),))
        with pytest.raises(ExpressionValidationError, match="event value"):
            pc.validate()


# ---------------------------------------------------------------------------
# PerformanceLayer
# ---------------------------------------------------------------------------


class TestPerformanceLayer:
    def test_empty(self) -> None:
        pl = PerformanceLayer.empty()
        assert pl.note_expressions == {}
        assert pl.section_rubato == {}
        assert pl.breath_marks == ()
        assert pl.pedal_curves == ()

    def test_empty_validates(self) -> None:
        PerformanceLayer.empty().validate()

    def test_for_note_found(self) -> None:
        nid: NoteId = ("piano", 0.0, 60)
        expr = NoteExpression(accent_strength=0.5)
        pl = PerformanceLayer(
            note_expressions={nid: expr},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )
        assert pl.for_note(nid) is expr

    def test_for_note_not_found(self) -> None:
        pl = PerformanceLayer.empty()
        assert pl.for_note(("piano", 0.0, 60)) is None

    def test_rubato_for_section(self) -> None:
        rc = RubatoCurve(section_name="verse", waypoints=((0.0, 1.0),))
        pl = PerformanceLayer(
            note_expressions={},
            section_rubato={"verse": rc},
            breath_marks=(),
            pedal_curves=(),
        )
        assert pl.rubato_for_section("verse") is rc
        assert pl.rubato_for_section("chorus") is None

    def test_pedals_for_instrument(self) -> None:
        pc1 = PedalCurve(cc_number=64, instrument="piano", events=((0.0, 127),))
        pc2 = PedalCurve(cc_number=64, instrument="organ", events=((0.0, 127),))
        pl = PerformanceLayer(
            note_expressions={},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(pc1, pc2),
        )
        assert pl.pedals_for_instrument("piano") == [pc1]
        assert pl.pedals_for_instrument("organ") == [pc2]
        assert pl.pedals_for_instrument("violin") == []

    def test_breaths_for_instrument_global(self) -> None:
        bm_global = BreathMark(beat_position=4.0, duration_beats=0.25)
        bm_violin = BreathMark(beat_position=8.0, duration_beats=0.25, instrument="violin")
        pl = PerformanceLayer(
            note_expressions={},
            section_rubato={},
            breath_marks=(bm_global, bm_violin),
            pedal_curves=(),
        )
        # Global breaths
        assert pl.breaths_for_instrument(None) == [bm_global]
        # Violin gets global + its own
        assert pl.breaths_for_instrument("violin") == [bm_global, bm_violin]
        # Piano gets only global
        assert pl.breaths_for_instrument("piano") == [bm_global]

    def test_validate_propagates_errors(self) -> None:
        bad_expr = NoteExpression(accent_strength=2.0)
        pl = PerformanceLayer(
            note_expressions={("piano", 0.0, 60): bad_expr},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )
        with pytest.raises(ExpressionValidationError):
            pl.validate()

    def test_validate_catches_bad_rubato(self) -> None:
        bad_rubato = RubatoCurve(section_name="verse", waypoints=((0.0, -1.0),))
        pl = PerformanceLayer(
            note_expressions={},
            section_rubato={"verse": bad_rubato},
            breath_marks=(),
            pedal_curves=(),
        )
        with pytest.raises(ExpressionValidationError):
            pl.validate()

    def test_validate_catches_bad_pedal(self) -> None:
        bad_pedal = PedalCurve(cc_number=200, instrument="piano", events=())
        pl = PerformanceLayer(
            note_expressions={},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(bad_pedal,),
        )
        with pytest.raises(ExpressionValidationError):
            pl.validate()

    def test_full_layer_validates(self) -> None:
        """A fully populated PerformanceLayer should validate cleanly."""
        nid: NoteId = ("piano", 0.0, 60)
        pl = PerformanceLayer(
            note_expressions={
                nid: NoteExpression(
                    legato_overlap=0.02,
                    accent_strength=0.6,
                    glissando_to=62,
                    pitch_bend_curve=((0.0, 0), (0.5, 4000), (1.0, 0)),
                    cc_curves={1: ((0.0, 0), (0.5, 80)), 11: ((0.0, 100),)},
                    micro_timing_ms=-3.0,
                    micro_dynamics=0.1,
                ),
            },
            section_rubato={
                "verse": RubatoCurve(
                    section_name="verse",
                    waypoints=((0.0, 0.95), (8.0, 1.05), (16.0, 1.0)),
                ),
            },
            breath_marks=(
                BreathMark(beat_position=16.0, duration_beats=0.25),
                BreathMark(beat_position=32.0, duration_beats=0.5, instrument="violin"),
            ),
            pedal_curves=(
                PedalCurve(
                    cc_number=64,
                    instrument="piano",
                    events=((0.0, 127), (3.5, 0), (4.0, 127), (7.5, 0)),
                ),
            ),
        )
        pl.validate()


# ---------------------------------------------------------------------------
# NoteId consistency with ScoreIR Note
# ---------------------------------------------------------------------------


class TestNoteIdConsistency:
    def test_note_id_matches_note_fields(self) -> None:
        """NoteId (instrument, start_beat, pitch) should match Note attributes."""
        from yao.ir.note import Note

        note = Note(pitch=60, start_beat=4.0, duration_beats=1.0, velocity=80, instrument="piano")
        nid: NoteId = (note.instrument, note.start_beat, note.pitch)
        assert nid == ("piano", 4.0, 60)

    def test_different_notes_different_ids(self) -> None:
        from yao.ir.note import Note

        n1 = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        n2 = Note(pitch=62, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        nid1: NoteId = (n1.instrument, n1.start_beat, n1.pitch)
        nid2: NoteId = (n2.instrument, n2.start_beat, n2.pitch)
        assert nid1 != nid2

    def test_lookup_via_note_id(self) -> None:
        """Demonstrate the overlay pattern: create NoteId from Note, look up expression."""
        from yao.ir.note import Note

        note = Note(pitch=60, start_beat=0.0, duration_beats=1.0, velocity=80, instrument="piano")
        nid: NoteId = (note.instrument, note.start_beat, note.pitch)
        expr = NoteExpression(accent_strength=0.7)
        pl = PerformanceLayer(
            note_expressions={nid: expr},
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )
        found = pl.for_note((note.instrument, note.start_beat, note.pitch))
        assert found is not None
        assert found.accent_strength == 0.7
