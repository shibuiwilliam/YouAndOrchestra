"""Tests for UserStyleProfile."""

from __future__ import annotations

from pathlib import Path

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.style_profile import StylePreference, UserStyleProfile
from yao.schema.feedback import FeedbackSeverity, FeedbackTag, HumanFeedbackEntry


class TestStyleProfile:
    def test_empty_profile(self) -> None:
        p = UserStyleProfile()
        assert p.user_id == "local"
        assert p.preferences == []

    def test_add_preference(self) -> None:
        p = UserStyleProfile()
        p.add_preference(StylePreference("tempo", (80, 120), 0.8, 5))
        assert p.get_preference("tempo") is not None
        assert p.get_preference("tempo").confidence == 0.8  # type: ignore[union-attr]

    def test_replace_preference(self) -> None:
        p = UserStyleProfile()
        p.add_preference(StylePreference("tempo", (80, 120), 0.5, 3))
        p.add_preference(StylePreference("tempo", (90, 130), 0.9, 10))
        assert len([x for x in p.preferences if x.dimension == "tempo"]) == 1
        assert p.get_preference("tempo").confidence == 0.9  # type: ignore[union-attr]

    def test_round_trip(self, tmp_path: Path) -> None:
        p = UserStyleProfile(user_id="test_user", total_annotations=10)
        p.add_preference(StylePreference("density", (0.3, 0.7), 0.85, 8))
        path = tmp_path / "profile.json"
        p.save(path)
        loaded = UserStyleProfile.load(path)
        assert loaded.user_id == "test_user"
        assert loaded.total_annotations == 10
        assert loaded.get_preference("density") is not None

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        loaded = UserStyleProfile.load(tmp_path / "missing.json")
        assert loaded.preferences == []


def _make_score(n_notes: int = 16, velocity: int = 80) -> ScoreIR:
    """Create a simple ScoreIR for testing."""
    notes = tuple(
        Note(pitch=60 + (i % 12), start_beat=float(i), duration_beats=0.9, velocity=velocity, instrument="piano")
        for i in range(n_notes)
    )
    return ScoreIR(
        title="Test",
        tempo_bpm=120.0,
        time_signature="4/4",
        key="C major",
        sections=(Section(name="verse", start_bar=0, end_bar=4, parts=(Part(instrument="piano", notes=notes),)),),
    )


class TestUpdateFrom:
    """Tests for UserStyleProfile.update_from()."""

    def test_positive_feedback_updates_dynamics(self) -> None:
        """'loved' feedback learns dynamics from the score."""
        profile = UserStyleProfile()
        score = _make_score(velocity=90)
        feedback = [
            HumanFeedbackEntry(bar=1, tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE),
            HumanFeedbackEntry(bar=2, tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE),
        ]
        profile.update_from(feedback, score)
        dyn = profile.get_preference("dynamics")
        assert dyn is not None
        assert dyn.preferred_range[0] <= 90 <= dyn.preferred_range[1]

    def test_sparse_feedback_increases_density_preference(self) -> None:
        """'too_sparse' feedback nudges density preference up."""
        profile = UserStyleProfile()
        score = _make_score(n_notes=8)
        feedback = [
            HumanFeedbackEntry(bar=1, tag=FeedbackTag.TOO_SPARSE, severity=FeedbackSeverity.MINOR),
        ]
        profile.update_from(feedback, score)
        density = profile.get_preference("density")
        assert density is not None
        # Preferred range should be above current density
        current_density = 8 / max(score.total_bars(), 1)
        assert density.preferred_range[1] > current_density

    def test_dense_feedback_decreases_density_preference(self) -> None:
        """'too_dense' feedback nudges density preference down."""
        profile = UserStyleProfile()
        score = _make_score(n_notes=32)
        feedback = [
            HumanFeedbackEntry(bar=1, tag=FeedbackTag.TOO_DENSE, severity=FeedbackSeverity.MINOR),
        ]
        profile.update_from(feedback, score)
        density = profile.get_preference("density")
        assert density is not None
        current_density = 32 / max(score.total_bars(), 1)
        assert density.preferred_range[0] < current_density

    def test_overall_quality_from_mixed_feedback(self) -> None:
        """Mixed feedback produces an overall quality signal."""
        profile = UserStyleProfile()
        score = _make_score()
        feedback = [
            HumanFeedbackEntry(bar=1, tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE),
            HumanFeedbackEntry(bar=2, tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE),
            HumanFeedbackEntry(bar=3, tag=FeedbackTag.BORING, severity=FeedbackSeverity.MINOR),
        ]
        profile.update_from(feedback, score)
        overall = profile.get_preference("overall")
        assert overall is not None
        avg = (overall.preferred_range[0] + overall.preferred_range[1]) / 2.0
        # 2 loved / 3 total = 6.67 quality signal
        assert avg > 5.0  # noqa: PLR2004

    def test_accumulated_annotations_count(self) -> None:
        """Total annotations accumulate across calls."""
        profile = UserStyleProfile()
        score = _make_score()
        fb1 = [HumanFeedbackEntry(bar=1, tag=FeedbackTag.LOVED, severity=FeedbackSeverity.POSITIVE)]
        fb2 = [HumanFeedbackEntry(bar=2, tag=FeedbackTag.BORING, severity=FeedbackSeverity.MINOR)]
        profile.update_from(fb1, score)
        profile.update_from(fb2, score)
        assert profile.total_annotations == 2

    def test_empty_feedback_no_change(self) -> None:
        """Empty feedback list does not modify profile."""
        profile = UserStyleProfile()
        score = _make_score()
        profile.update_from([], score)
        assert profile.total_annotations == 0
        assert len(profile.preferences) == 0
