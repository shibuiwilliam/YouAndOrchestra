"""Tests for the project fingerprint module."""

from __future__ import annotations

from pathlib import Path

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.reflect.project_fingerprint import (
    ProjectFingerprint,
    compute_fingerprint,
    fingerprint_distance,
    load_fingerprint,
    save_fingerprint,
)


def _make_score(pitches: list[int], velocities: list[int], tempo: float = 120.0) -> ScoreIR:
    """Create a minimal ScoreIR for testing."""
    notes = tuple(
        Note(
            pitch=p,
            start_beat=float(i),
            duration_beats=1.0,
            velocity=v,
            instrument="piano",
        )
        for i, (p, v) in enumerate(zip(pitches, velocities, strict=True))
    )
    parts = (Part(instrument="piano", notes=notes),)
    sections = (Section(name="A", start_bar=0, end_bar=4, parts=parts),)
    return ScoreIR(
        title="test",
        tempo_bpm=tempo,
        time_signature="4/4",
        key="C major",
        sections=sections,
    )


class TestComputeFingerprint:
    """Tests for fingerprint computation."""

    def test_empty_scores_returns_default(self) -> None:
        """Empty score list should return default fingerprint."""
        fp = compute_fingerprint("test", [])
        assert fp.project_id == "test"
        assert fp.iteration_count == 0

    def test_single_score_fingerprint(self) -> None:
        """Single score should produce valid fingerprint."""
        score = _make_score([60, 62, 64, 65], [80, 85, 90, 75])
        fp = compute_fingerprint("test", [score])
        assert fp.iteration_count == 1
        assert fp.avg_velocity > 0
        assert fp.pitch_center > 0

    def test_multiple_scores_averaged(self) -> None:
        """Multiple scores should produce averaged fingerprint."""
        s1 = _make_score([60, 62, 64, 65], [80, 85, 90, 75], tempo=100.0)
        s2 = _make_score([60, 62, 64, 65], [80, 85, 90, 75], tempo=140.0)
        fp = compute_fingerprint("test", [s1, s2])
        assert fp.iteration_count == 2
        assert abs(fp.avg_tempo - 120.0) < 0.1

    def test_genre_preserved(self) -> None:
        """Genre should be stored in fingerprint."""
        fp = compute_fingerprint("test", [], genre="jazz")
        assert fp.genre == "jazz"


class TestFingerprintDistance:
    """Tests for fingerprint comparison."""

    def test_identical_fingerprints_zero_distance(self) -> None:
        """Identical fingerprints should have zero distance."""
        fp = ProjectFingerprint(project_id="a", avg_tempo=120.0, avg_velocity=80.0)
        assert fingerprint_distance(fp, fp) == 0.0

    def test_different_fingerprints_positive_distance(self) -> None:
        """Different fingerprints should have positive distance."""
        fp1 = ProjectFingerprint(project_id="a", avg_tempo=80.0, avg_velocity=60.0)
        fp2 = ProjectFingerprint(project_id="b", avg_tempo=140.0, avg_velocity=100.0)
        assert fingerprint_distance(fp1, fp2) > 0

    def test_symmetric(self) -> None:
        """Distance should be symmetric."""
        fp1 = ProjectFingerprint(project_id="a", avg_tempo=80.0)
        fp2 = ProjectFingerprint(project_id="b", avg_tempo=140.0)
        assert abs(fingerprint_distance(fp1, fp2) - fingerprint_distance(fp2, fp1)) < 1e-10


class TestFingerprintPersistence:
    """Tests for save/load."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        """Save then load should produce equivalent fingerprint."""
        fp = ProjectFingerprint(
            project_id="test_proj",
            genre="rock",
            avg_tempo=130.0,
            avg_density=5.0,
            avg_velocity=90.0,
            velocity_range=40.0,
            pitch_center=65.0,
            pitch_spread=8.5,
            leap_ratio=0.3,
            swing_indicator=0.1,
            iteration_count=3,
        )
        path = tmp_path / "fp.json"
        save_fingerprint(fp, path)
        loaded = load_fingerprint(path)

        assert loaded.project_id == fp.project_id
        assert loaded.genre == fp.genre
        assert loaded.avg_tempo == fp.avg_tempo
        assert loaded.iteration_count == fp.iteration_count
