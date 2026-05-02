"""Tests for audio feedback adaptation logic."""

from __future__ import annotations

from yao.conductor.audio_feedback import (
    AudioAdaptation,
    AudioThresholds,
    apply_audio_adaptations,
    apply_dynamics_adaptation,
    suggest_audio_adaptations,
)
from yao.perception.audio_features import BandName, PerceptualReport


def _make_report(
    *,
    lufs: float = -16.0,
    masking: float = 0.1,
) -> PerceptualReport:
    """Build a minimal PerceptualReport for testing."""
    return PerceptualReport(
        lufs_integrated=lufs,
        lufs_short_term=(),
        peak_dbfs=-1.0,
        dynamic_range_db=10.0,
        spectral_centroid_mean=2000.0,
        spectral_centroid_per_section={},
        spectral_rolloff=8000.0,
        spectral_flatness=0.3,
        onset_density_per_section={},
        tempo_stability_ms_drift=5.0,
        frequency_band_energy={band: 1.0 / 7.0 for band in BandName},
        masking_risk_score=masking,
    )


class TestSuggestAudioAdaptations:
    """Tests for suggest_audio_adaptations()."""

    def test_no_adaptations_when_within_tolerance(self) -> None:
        report = _make_report(lufs=-16.0, masking=0.1)
        thresholds = AudioThresholds(lufs_target=-16.0, lufs_tolerance=2.0, masking_risk_max=0.3)
        result = suggest_audio_adaptations(report, thresholds)
        assert len(result) == 0

    def test_dynamics_adjust_when_too_quiet(self) -> None:
        report = _make_report(lufs=-22.0)
        thresholds = AudioThresholds(lufs_target=-16.0, lufs_tolerance=2.0)
        result = suggest_audio_adaptations(report, thresholds)
        assert len(result) >= 1
        assert result[0].type == "dynamics_adjust"
        assert result[0].parameters["direction"] == "up"
        assert result[0].parameters["velocity_scale"] > 1.0

    def test_dynamics_adjust_when_too_loud(self) -> None:
        report = _make_report(lufs=-10.0)
        thresholds = AudioThresholds(lufs_target=-16.0, lufs_tolerance=2.0)
        result = suggest_audio_adaptations(report, thresholds)
        assert len(result) >= 1
        assert result[0].type == "dynamics_adjust"
        assert result[0].parameters["direction"] == "down"
        assert result[0].parameters["velocity_scale"] < 1.0

    def test_register_adjust_when_masking_high(self) -> None:
        report = _make_report(masking=0.5)
        thresholds = AudioThresholds(masking_risk_max=0.3)
        result = suggest_audio_adaptations(report, thresholds)
        assert any(a.type == "register_adjust" for a in result)

    def test_no_register_adjust_when_masking_low(self) -> None:
        report = _make_report(masking=0.1)
        thresholds = AudioThresholds(masking_risk_max=0.3)
        result = suggest_audio_adaptations(report, thresholds)
        assert not any(a.type == "register_adjust" for a in result)

    def test_multiple_adaptations(self) -> None:
        report = _make_report(lufs=-22.0, masking=0.5)
        thresholds = AudioThresholds(lufs_target=-16.0, lufs_tolerance=2.0, masking_risk_max=0.3)
        result = suggest_audio_adaptations(report, thresholds)
        types = [a.type for a in result]
        assert "dynamics_adjust" in types
        assert "register_adjust" in types

    def test_velocity_scale_capped(self) -> None:
        """Velocity scale should not exceed 1.3 even for very quiet audio."""
        report = _make_report(lufs=-40.0)
        thresholds = AudioThresholds(lufs_target=-16.0, lufs_tolerance=2.0)
        result = suggest_audio_adaptations(report, thresholds)
        assert result[0].parameters["velocity_scale"] <= 1.3


def _make_score(
    *,
    velocities: tuple[int, ...] = (80, 100),
    pitches: tuple[int, ...] = (60, 64),
):
    """Build a minimal ScoreIR for testing adaptations."""
    from yao.ir.note import Note
    from yao.ir.score_ir import Part, ScoreIR, Section

    notes = tuple(
        Note(pitch=p, start_beat=float(i), duration_beats=1.0, velocity=v, instrument="piano")
        for i, (p, v) in enumerate(zip(pitches, velocities, strict=True))
    )
    part = Part(instrument="piano", notes=notes)
    section = Section(name="verse", start_bar=0, end_bar=2, parts=(part,))
    return ScoreIR(title="Test", tempo_bpm=120.0, time_signature="4/4", key="C major", sections=(section,))


class TestApplyDynamicsAdaptation:
    """Tests for apply_dynamics_adaptation()."""

    def test_apply_dynamics_scales_velocities(self) -> None:
        score = _make_score(velocities=(80, 100))

        adaptation = AudioAdaptation(
            type="dynamics_adjust",
            parameters={"velocity_scale": 1.2, "direction": "up"},
            reason="test",
        )

        new_score = apply_dynamics_adaptation(score, adaptation)
        new_vels = [n.velocity for n in new_score.sections[0].parts[0].notes]
        assert new_vels[0] == 96  # 80 * 1.2
        assert new_vels[1] == 120  # 100 * 1.2

    def test_velocity_clipped_to_127(self) -> None:
        score = _make_score(velocities=(120,), pitches=(60,))

        adaptation = AudioAdaptation(
            type="dynamics_adjust",
            parameters={"velocity_scale": 1.3, "direction": "up"},
            reason="test",
        )

        new_score = apply_dynamics_adaptation(score, adaptation)
        assert new_score.sections[0].parts[0].notes[0].velocity == 127


class TestApplyAudioAdaptations:
    """Tests for apply_audio_adaptations()."""

    def test_applies_dynamics_adaptation(self) -> None:
        score = _make_score(velocities=(80,), pitches=(60,))

        adaptations = [
            AudioAdaptation(
                type="dynamics_adjust",
                parameters={"velocity_scale": 1.1, "direction": "up"},
                reason="louder",
            ),
        ]

        new_score = apply_audio_adaptations(score, adaptations)
        assert new_score.sections[0].parts[0].notes[0].velocity == 88  # 80 * 1.1
