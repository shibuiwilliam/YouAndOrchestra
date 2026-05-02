"""Tests for counter-melody generator."""

from __future__ import annotations

from yao.generators.counter_melody import generate_counter_melody
from yao.ir.note import Note
from yao.ir.score_ir import Part


def _make_main_part(pitches: list[int], start_beat: float = 0.0) -> Part:
    """Create a simple main melody Part from pitch list."""
    notes = []
    for i, p in enumerate(pitches):
        notes.append(
            Note(
                pitch=p,
                start_beat=start_beat + i * 1.0,
                duration_beats=0.9,
                velocity=80,
                instrument="piano",
            )
        )
    return Part(instrument="piano", notes=tuple(notes))


class TestCounterMelodyBasics:
    """Test basic counter-melody generation."""

    def test_generates_notes(self) -> None:
        main = _make_main_part([60, 62, 64, 65, 67, 65, 64, 62])
        counter, prov = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=1.0,
            seed=42,
        )
        assert len(counter.notes) > 0
        assert counter.instrument == "violin"
        assert len(prov.records) >= 2  # noqa: PLR2004

    def test_density_factor_controls_note_count(self) -> None:
        main = _make_main_part([60, 62, 64, 65, 67, 65, 64, 62] * 2)

        full, _ = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=1.0,
            seed=42,
        )
        half, _ = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=0.3,
            seed=42,
        )

        assert len(half.notes) < len(full.notes)

    def test_deterministic_with_same_seed(self) -> None:
        main = _make_main_part([60, 64, 67, 72, 71, 67, 64, 60])
        a, _ = generate_counter_melody(main, "violin", "C major", 120.0, "4/4", seed=42)
        b, _ = generate_counter_melody(main, "violin", "C major", 120.0, "4/4", seed=42)
        assert len(a.notes) == len(b.notes)
        for na, nb in zip(a.notes, b.notes, strict=True):
            assert na.pitch == nb.pitch

    def test_different_seed_different_output(self) -> None:
        main = _make_main_part([60, 64, 67, 72, 71, 67, 64, 60])
        a, _ = generate_counter_melody(main, "violin", "C major", 120.0, "4/4", seed=42)
        b, _ = generate_counter_melody(main, "violin", "C major", 120.0, "4/4", seed=99)
        # Should produce at least some different pitches
        a_pitches = [n.pitch for n in a.notes]
        b_pitches = [n.pitch for n in b.notes]
        assert a_pitches != b_pitches or len(a.notes) != len(b.notes)


class TestCounterpointPrinciples:
    """Test species counterpoint principles."""

    def test_consonance_on_strong_beats(self) -> None:
        """Strong beat notes should be consonant with main melody."""
        main = _make_main_part([60, 62, 64, 65, 67, 69, 71, 72])
        counter, _ = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=1.0,
            seed=42,
        )

        consonant_intervals = {0, 3, 4, 5, 7, 8, 9}
        strong_beat_consonant = 0
        strong_beat_total = 0

        for cn in counter.notes:
            beat_in_bar = cn.start_beat % 4
            if beat_in_bar % 2 < 0.01:  # strong beat
                # Find the main note at this beat
                for mn in main.notes:
                    if abs(mn.start_beat - cn.start_beat) < 0.01:
                        interval = abs(cn.pitch - mn.pitch) % 12
                        strong_beat_total += 1
                        if interval in consonant_intervals:
                            strong_beat_consonant += 1
                        break

        if strong_beat_total > 0:
            ratio = strong_beat_consonant / strong_beat_total
            assert ratio >= 0.8, (  # noqa: PLR2004
                f"Strong beat consonance ratio {ratio:.2f} too low (expected >= 0.8)"
            )

    def test_contrary_motion_preferred(self) -> None:
        """Counter-melody should move contrary to main melody more often than parallel."""
        # Ascending main melody — counter should tend downward
        main = _make_main_part([60, 62, 64, 65, 67, 69, 71, 72])
        counter, _ = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=1.0,
            seed=42,
        )

        if len(counter.notes) < 3:  # noqa: PLR2004
            return

        contrary_count = 0
        parallel_count = 0

        counter_list = list(counter.notes)
        main_list = list(main.notes)

        for i in range(1, min(len(counter_list), len(main_list))):
            main_motion = main_list[i].pitch - main_list[i - 1].pitch
            counter_motion = counter_list[i].pitch - counter_list[i - 1].pitch

            if main_motion == 0 or counter_motion == 0:
                continue

            if (main_motion > 0) != (counter_motion > 0):
                contrary_count += 1
            else:
                parallel_count += 1

        total = contrary_count + parallel_count
        if total > 3:  # noqa: PLR2004
            assert contrary_count >= parallel_count, (
                f"Contrary motion ({contrary_count}) should be >= parallel ({parallel_count})"
            )

    def test_no_unison_with_main(self) -> None:
        """Counter-melody should not have exact same pitch as main melody."""
        main = _make_main_part([60, 64, 67, 72])
        counter, _ = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=1.0,
            seed=42,
        )
        for cn in counter.notes:
            for mn in main.notes:
                if abs(cn.start_beat - mn.start_beat) < 0.01:
                    assert cn.pitch != mn.pitch

    def test_counter_velocity_lower_than_main(self) -> None:
        """Counter-melody velocity should be softer than main melody."""
        main = _make_main_part([60, 64, 67, 72, 71, 67, 64, 60])
        counter, _ = generate_counter_melody(
            main,
            "violin",
            "C major",
            120.0,
            "4/4",
            density_factor=1.0,
            seed=42,
        )
        if counter.notes:
            avg_main_vel = sum(n.velocity for n in main.notes) / len(main.notes)
            avg_counter_vel = sum(n.velocity for n in counter.notes) / len(counter.notes)
            assert avg_counter_vel < avg_main_vel
