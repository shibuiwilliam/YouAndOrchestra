"""Tests for GrooveApplicator (Layer 2).

Tests cover:
- Groove changes note timings
- Two different grooves produce different MIDI
- apply_to_all_instruments=False only affects drums
- Velocity multiplication works
- Provenance is recorded
- Backward compatibility (no groove = unchanged)
- Reproducibility via seed
"""

from __future__ import annotations

from yao.generators.groove_applicator import apply_groove
from yao.ir.groove import GrooveProfile
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section


def _make_score(
    instruments: list[str] | None = None,
    notes_per_part: int = 16,
) -> ScoreIR:
    """Create a test ScoreIR with evenly spaced notes."""
    if instruments is None:
        instruments = ["piano", "drums"]

    parts: list[Part] = []
    for instr in instruments:
        notes = tuple(
            Note(
                pitch=60 if instr != "drums" else 36,
                start_beat=float(i),
                duration_beats=0.5,
                velocity=80,
                instrument=instr,
            )
            for i in range(notes_per_part)
        )
        parts.append(Part(instrument=instr, notes=notes))

    section = Section(
        name="test",
        start_bar=0,
        end_bar=notes_per_part // 4,
        parts=tuple(parts),
    )
    return ScoreIR(
        title="test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(section,),
    )


def _make_groove(**kwargs: object) -> GrooveProfile:
    defaults: dict[str, object] = {
        "name": "test_groove",
        "microtiming": {0: 5.0, 4: -3.0, 8: 8.0, 12: -5.0},
        "velocity_pattern": {0: 1.2, 4: 0.8, 8: 1.1, 12: 0.9},
        "ghost_probability": 0.0,
        "swing_ratio": 0.5,
        "timing_jitter_sigma": 0.0,  # No jitter for deterministic tests
    }
    defaults.update(kwargs)
    return GrooveProfile(**defaults)  # type: ignore[arg-type]


class TestGrooveApplicator:
    """Tests for apply_groove."""

    def test_groove_changes_timings(self) -> None:
        """Applying groove changes note start times."""
        score = _make_score()
        groove = _make_groove()
        grooved, _prov = apply_groove(score, groove)

        original_times = [n.start_beat for n in score.all_notes()]
        grooved_times = [n.start_beat for n in grooved.all_notes()]
        assert original_times != grooved_times

    def test_two_grooves_differ(self) -> None:
        """Two different groove profiles produce different results."""
        score = _make_score()
        groove_a = _make_groove(name="groove_a", microtiming={0: 10.0})
        groove_b = _make_groove(name="groove_b", microtiming={0: -10.0})

        grooved_a, _ = apply_groove(score, groove_a)
        grooved_b, _ = apply_groove(score, groove_b)

        times_a = [n.start_beat for n in grooved_a.all_notes()]
        times_b = [n.start_beat for n in grooved_b.all_notes()]
        assert times_a != times_b

    def test_apply_to_all_true(self) -> None:
        """With apply_to_all_instruments=True, all parts get groove."""
        score = _make_score(instruments=["piano", "drums"])
        groove = _make_groove(apply_to_all_instruments=True)
        grooved, _ = apply_groove(score, groove)

        orig_piano = score.part_for_instrument("piano")
        grooved_piano = grooved.part_for_instrument("piano")

        orig_times = [n.start_beat for n in orig_piano]
        grooved_times = [n.start_beat for n in grooved_piano]
        assert orig_times != grooved_times

    def test_apply_drums_only(self) -> None:
        """With apply_to_all_instruments=False, only drums are affected."""
        score = _make_score(instruments=["piano", "drums"])
        groove = _make_groove(apply_to_all_instruments=False)
        grooved, _ = apply_groove(score, groove)

        # Piano should be unchanged
        orig_piano = score.part_for_instrument("piano")
        grooved_piano = grooved.part_for_instrument("piano")
        orig_piano_times = [n.start_beat for n in orig_piano]
        grooved_piano_times = [n.start_beat for n in grooved_piano]
        assert orig_piano_times == grooved_piano_times

        # Drums should be changed
        orig_drums = score.part_for_instrument("drums")
        grooved_drums = grooved.part_for_instrument("drums")
        orig_drum_times = [n.start_beat for n in orig_drums]
        grooved_drum_times = [n.start_beat for n in grooved_drums]
        assert orig_drum_times != grooved_drum_times

    def test_velocity_multiplication(self) -> None:
        """Velocity is multiplied by the pattern."""
        score = _make_score(instruments=["piano"], notes_per_part=4)
        groove = _make_groove(
            microtiming={},  # No timing changes
            velocity_pattern={0: 1.5},  # Strong accent on beat 0
            timing_jitter_sigma=0.0,
        )
        grooved, _ = apply_groove(score, groove)

        # Beat 0 note should have higher velocity
        orig_notes = score.all_notes()
        grooved_notes = grooved.all_notes()
        beat0_orig = [n for n in orig_notes if n.start_beat == 0.0][0]
        beat0_grooved = [n for n in grooved_notes if abs(n.start_beat) < 0.1][0]
        assert beat0_grooved.velocity > beat0_orig.velocity

    def test_velocity_clamped(self) -> None:
        """Velocity is clamped to [1, 127]."""
        score = _make_score(instruments=["piano"], notes_per_part=4)
        groove = _make_groove(
            microtiming={},
            velocity_pattern={0: 2.0},  # Would push 80 → 160
            timing_jitter_sigma=0.0,
        )
        grooved, _ = apply_groove(score, groove)
        for note in grooved.all_notes():
            assert 1 <= note.velocity <= 127

    def test_provenance_recorded(self) -> None:
        """Provenance log records the groove application."""
        score = _make_score()
        groove = _make_groove()
        _, prov = apply_groove(score, groove)

        assert len(prov.records) == 1
        record = prov.records[0]
        assert record.operation == "groove_application"
        assert "test_groove" in record.rationale

    def test_reproducibility_with_seed(self) -> None:
        """Same seed produces identical results."""
        score = _make_score()
        groove = _make_groove(timing_jitter_sigma=5.0)

        grooved_a, _ = apply_groove(score, groove, seed=123)
        grooved_b, _ = apply_groove(score, groove, seed=123)

        times_a = [n.start_beat for n in grooved_a.all_notes()]
        times_b = [n.start_beat for n in grooved_b.all_notes()]
        assert times_a == times_b

    def test_different_seeds_differ(self) -> None:
        """Different seeds produce different results when jitter > 0."""
        score = _make_score()
        groove = _make_groove(timing_jitter_sigma=5.0)

        grooved_a, _ = apply_groove(score, groove, seed=1)
        grooved_b, _ = apply_groove(score, groove, seed=2)

        times_a = [n.start_beat for n in grooved_a.all_notes()]
        times_b = [n.start_beat for n in grooved_b.all_notes()]
        assert times_a != times_b

    def test_empty_score_no_error(self) -> None:
        """Empty score produces empty grooved score."""
        score = ScoreIR(
            title="empty",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(),
        )
        groove = _make_groove()
        grooved, prov = apply_groove(score, groove)
        assert len(grooved.sections) == 0

    def test_no_groove_identity(self) -> None:
        """A groove with no offsets and no jitter is identity."""
        score = _make_score()
        null_groove = GrooveProfile(
            name="null",
            microtiming={},
            velocity_pattern={},
            timing_jitter_sigma=0.0,
        )
        grooved, _ = apply_groove(score, null_groove)

        orig_times = [(n.start_beat, n.velocity) for n in score.all_notes()]
        grooved_data = [(n.start_beat, n.velocity) for n in grooved.all_notes()]
        assert orig_times == grooved_data

    def test_preserves_metadata(self) -> None:
        """Groove preserves title, tempo, key, time signature."""
        score = _make_score()
        groove = _make_groove()
        grooved, _ = apply_groove(score, groove)

        assert grooved.title == score.title
        assert grooved.tempo_bpm == score.tempo_bpm
        assert grooved.time_signature == score.time_signature
        assert grooved.key == score.key


class TestSwingApplication:
    """Swing (swing_ratio) must actually shift off-beat 8th notes (P0.3).

    Regression for the swing dead-wire: swing_ratio was recorded to
    provenance but never applied to pitched-note timing.
    """

    def _offbeat_score(self) -> ScoreIR:
        """A single part with notes on every 8th (beats 0, 0.5, 1, 1.5, ...)."""
        notes = tuple(
            Note(
                pitch=60,
                start_beat=i * 0.5,
                duration_beats=0.25,
                velocity=80,
                instrument="piano",
            )
            for i in range(8)
        )
        section = Section(
            name="s",
            start_bar=0,
            end_bar=1,
            parts=(Part(instrument="piano", notes=notes),),
        )
        return ScoreIR(
            title="swing",
            tempo_bpm=120.0,
            time_signature="4/4",
            key="C major",
            sections=(section,),
        )

    def test_offbeat_eighths_are_delayed(self) -> None:
        """Off-beat 8ths (0.5, 1.5, ...) shift later; downbeats stay put."""
        score = self._offbeat_score()
        # No microtiming/jitter so we isolate the swing effect.
        groove = _make_groove(microtiming={}, velocity_pattern={}, swing_ratio=0.667)
        grooved, _ = apply_groove(score, groove)

        starts = sorted(n.start_beat for n in grooved.all_notes())
        # swing_amount = (0.667 - 0.5) * 2 = 0.334; shift = 0.334 * 0.25 ≈ 0.0835
        expected_shift = (0.667 - 0.5) * 2.0 * 0.25
        # On-beat notes (0.0, 1.0, 2.0, 3.0) unchanged.
        for onbeat in (0.0, 1.0, 2.0, 3.0):
            assert any(abs(s - onbeat) < 1e-6 for s in starts), f"on-beat {onbeat} missing/moved"
        # Off-beat notes moved to 0.5+shift, 1.5+shift, ...
        for offbeat in (0.5, 1.5, 2.5, 3.5):
            target = offbeat + expected_shift
            assert any(abs(s - target) < 1e-6 for s in starts), f"off-beat {offbeat} not swung to {target}"

    def test_straight_groove_leaves_offbeats_unchanged(self) -> None:
        """swing_ratio=0.5 (straight) shifts nothing."""
        score = self._offbeat_score()
        groove = _make_groove(microtiming={}, velocity_pattern={}, swing_ratio=0.5)
        grooved, _ = apply_groove(score, groove)

        orig = sorted(n.start_beat for n in score.all_notes())
        got = sorted(n.start_beat for n in grooved.all_notes())
        assert orig == got

    def test_swing_recorded_in_provenance(self) -> None:
        """Provenance reports how many off-beats were swung."""
        score = self._offbeat_score()
        groove = _make_groove(microtiming={}, velocity_pattern={}, swing_ratio=0.667)
        _, prov = apply_groove(score, groove)
        rec = next(r for r in prov.records if r.operation == "groove_application")
        assert rec.parameters["swung_notes"] == 4
        assert rec.parameters["swing_amount"] > 0.0

    def test_swing_is_deterministic(self) -> None:
        """Same inputs → identical swung output."""
        score = self._offbeat_score()
        groove = _make_groove(microtiming={}, velocity_pattern={}, swing_ratio=0.6)
        a, _ = apply_groove(score, groove, seed=1)
        b, _ = apply_groove(score, groove, seed=1)
        assert [n.start_beat for n in a.all_notes()] == [n.start_beat for n in b.all_notes()]
