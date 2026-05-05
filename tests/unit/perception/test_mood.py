"""Tests for D2 MoodProfile — multi-dimensional mood representation."""

from __future__ import annotations

import pytest

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.mood import MoodProfile, estimate_mood_from_score


class TestMoodProfile:
    """Tests for MoodProfile dataclass."""

    def test_default_values(self) -> None:
        mood = MoodProfile()
        assert mood.arousal == 0.0
        assert mood.valence == 0.0

    def test_frozen(self) -> None:
        mood = MoodProfile(arousal=0.5)
        with pytest.raises(AttributeError):
            mood.arousal = 0.8  # type: ignore[misc]

    def test_distance_to_self_is_zero(self) -> None:
        mood = MoodProfile(arousal=0.5, valence=-0.3, tension=0.7)
        assert mood.distance(mood) == 0.0

    def test_distance_symmetric(self) -> None:
        a = MoodProfile(arousal=0.5, valence=0.3)
        b = MoodProfile(arousal=-0.2, valence=0.8)
        assert abs(a.distance(b) - b.distance(a)) < 1e-10

    def test_distance_positive(self) -> None:
        a = MoodProfile(arousal=1.0, valence=1.0)
        b = MoodProfile(arousal=-1.0, valence=-1.0)
        assert a.distance(b) > 0

    def test_similar_moods_small_distance(self) -> None:
        a = MoodProfile(arousal=0.5, valence=0.3, tension=0.6)
        b = MoodProfile(arousal=0.52, valence=0.31, tension=0.59)
        assert a.distance(b) < 0.1

    def test_round_trip(self) -> None:
        mood = MoodProfile(arousal=0.5, valence=-0.3, tension=0.7, intimacy=0.4)
        restored = MoodProfile.from_dict(mood.to_dict())
        assert mood.distance(restored) < 1e-10


class TestEstimateMoodFromScore:
    """Tests for D2 estimate_mood_from_score."""

    def _make_energetic_score(self) -> ScoreIR:
        notes = tuple(
            Note(pitch=72 + (i % 12), start_beat=i * 0.25, duration_beats=0.25, velocity=110, instrument="piano")
            for i in range(48)
        )
        return ScoreIR(
            title="energetic",
            tempo_bpm=140,
            time_signature="4/4",
            key="C major",
            sections=(Section(name="A", start_bar=0, end_bar=3, parts=(Part(instrument="piano", notes=notes),)),),
        )

    def _make_calm_score(self) -> ScoreIR:
        notes = tuple(
            Note(pitch=55 + (i % 5), start_beat=i * 2.0, duration_beats=1.5, velocity=40, instrument="piano")
            for i in range(6)
        )
        return ScoreIR(
            title="calm",
            tempo_bpm=60,
            time_signature="4/4",
            key="A minor",
            sections=(Section(name="A", start_bar=0, end_bar=3, parts=(Part(instrument="piano", notes=notes),)),),
        )

    def test_energetic_has_positive_arousal(self) -> None:
        mood = estimate_mood_from_score(self._make_energetic_score())
        assert mood.arousal > 0.0

    def test_calm_has_negative_arousal(self) -> None:
        mood = estimate_mood_from_score(self._make_calm_score())
        assert mood.arousal < 0.0

    def test_energetic_higher_aggression_than_calm(self) -> None:
        energetic = estimate_mood_from_score(self._make_energetic_score())
        calm = estimate_mood_from_score(self._make_calm_score())
        assert energetic.aggression > calm.aggression

    def test_calm_higher_intimacy_than_energetic(self) -> None:
        energetic = estimate_mood_from_score(self._make_energetic_score())
        calm = estimate_mood_from_score(self._make_calm_score())
        assert calm.intimacy > energetic.intimacy

    def test_empty_score(self) -> None:
        score = ScoreIR(title="empty", tempo_bpm=120, time_signature="4/4", key="C major", sections=())
        mood = estimate_mood_from_score(score)
        assert mood.arousal == -1.0  # 0 mapped to -1
        assert mood.tension == 0.0

    def test_all_dimensions_bounded(self) -> None:
        mood = estimate_mood_from_score(self._make_energetic_score())
        assert -1.0 <= mood.arousal <= 1.0
        assert -1.0 <= mood.valence <= 1.0
        assert 0.0 <= mood.tension <= 1.0
        assert 0.0 <= mood.intimacy <= 1.0
        assert 0.0 <= mood.grandeur <= 1.0
        assert 0.0 <= mood.aggression <= 1.0
