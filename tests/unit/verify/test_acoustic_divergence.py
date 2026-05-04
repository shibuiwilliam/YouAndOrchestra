"""Tests for acoustic divergence critique rules."""

from __future__ import annotations

from yao.perception.audio_features import BandName, PerceptualReport
from yao.verify.acoustic.divergence_rules import (
    BrightnessIntentMismatchDetector,
    EnergyTrajectoryViolationDetector,
    LufsTargetViolationDetector,
    SpectralImbalanceDetector,
    SymbolicAcousticDivergenceDetector,
)
from yao.verify.critique.types import Role, Severity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_report(
    *,
    lufs: float = -16.0,
    dynamic_range: float = 6.0,
    masking: float = 0.1,
    spectral_centroid: float = 2000.0,
    flatness: float = 0.1,
    peak_dbfs: float = -3.0,
    band_energy: dict[BandName, float] | None = None,
) -> PerceptualReport:
    """Create a minimal PerceptualReport for testing."""
    if band_energy is None:
        band_energy = {
            BandName.SUB_BASS: 0.05,
            BandName.BASS: 0.15,
            BandName.LOW_MID: 0.20,
            BandName.MID: 0.25,
            BandName.HIGH_MID: 0.15,
            BandName.PRESENCE: 0.10,
            BandName.BRILLIANCE: 0.10,
        }
    return PerceptualReport(
        lufs_integrated=lufs,
        lufs_short_term=((0.0, lufs), (3.0, lufs + 1), (6.0, lufs - 1)),
        peak_dbfs=peak_dbfs,
        dynamic_range_db=dynamic_range,
        spectral_centroid_mean=spectral_centroid,
        spectral_centroid_per_section={"full": spectral_centroid},
        spectral_rolloff=8000.0,
        spectral_flatness=flatness,
        onset_density_per_section={"full": 3.0},
        tempo_stability_ms_drift=10.0,
        frequency_band_energy=band_energy,
        masking_risk_score=masking,
    )


# ---------------------------------------------------------------------------
# SymbolicAcousticDivergenceDetector
# ---------------------------------------------------------------------------


class TestSymbolicAcousticDivergence:
    def test_no_finding_when_both_good(self) -> None:
        """No divergence when both symbolic and acoustic are healthy."""
        report = _make_report(masking=0.1, lufs=-16.0)
        detector = SymbolicAcousticDivergenceDetector()
        findings = detector.detect(report, symbolic_pass_rate=0.9, symbolic_quality_score=8.0)
        assert len(findings) == 0

    def test_no_finding_when_both_bad(self) -> None:
        """No divergence finding when both are bad (that's consistency)."""
        report = _make_report(masking=0.9, lufs=-50.0)
        detector = SymbolicAcousticDivergenceDetector()
        findings = detector.detect(report, symbolic_pass_rate=0.3, symbolic_quality_score=3.0)
        assert len(findings) == 0

    def test_critical_finding_when_symbolic_high_acoustic_low(self) -> None:
        """Fires critical when symbolic is high but acoustic is poor."""
        # High masking + bad LUFS + imbalanced bands = poor acoustic quality
        report = _make_report(
            masking=0.9,
            lufs=-50.0,
            band_energy={
                BandName.SUB_BASS: 0.01,
                BandName.BASS: 0.01,
                BandName.LOW_MID: 0.01,
                BandName.MID: 0.90,  # extreme imbalance
                BandName.HIGH_MID: 0.03,
                BandName.PRESENCE: 0.02,
                BandName.BRILLIANCE: 0.02,
            },
        )
        detector = SymbolicAcousticDivergenceDetector()
        findings = detector.detect(report, symbolic_pass_rate=0.95, symbolic_quality_score=9.0)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.CRITICAL
        assert findings[0].role == Role.ACOUSTIC
        assert "symbolic" in findings[0].issue.lower()

    def test_major_finding_when_acoustic_high_symbolic_low(self) -> None:
        """Fires major when acoustic is good but symbolic is weak."""
        report = _make_report(masking=0.05, lufs=-16.0)
        detector = SymbolicAcousticDivergenceDetector()
        findings = detector.detect(report, symbolic_pass_rate=0.2, symbolic_quality_score=2.0)
        assert len(findings) >= 1
        assert findings[0].severity == Severity.MAJOR

    def test_evidence_includes_scores(self) -> None:
        """Evidence contains both symbolic and acoustic scores."""
        report = _make_report(masking=0.9, lufs=-50.0)
        detector = SymbolicAcousticDivergenceDetector()
        findings = detector.detect(report, symbolic_pass_rate=0.9, symbolic_quality_score=8.5)
        if findings:
            evidence = findings[0].evidence
            assert "symbolic_pass_rate" in evidence
            assert "acoustic_quality_proxy" in evidence


# ---------------------------------------------------------------------------
# LufsTargetViolationDetector
# ---------------------------------------------------------------------------


class TestLufsTargetViolation:
    def test_no_finding_within_tolerance(self) -> None:
        """No finding when LUFS is within tolerance of target."""
        report = _make_report(lufs=-15.0)
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report, target_lufs=-14.0, tolerance=3.0)
        assert len(findings) == 0

    def test_finding_when_too_loud(self) -> None:
        """Finding when LUFS exceeds target + tolerance."""
        report = _make_report(lufs=-8.0)
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report, target_lufs=-14.0, tolerance=3.0)
        assert len(findings) == 1
        assert "too loud" in findings[0].issue

    def test_finding_when_too_quiet(self) -> None:
        """Finding when LUFS is below target - tolerance."""
        report = _make_report(lufs=-22.0)
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report, target_lufs=-14.0, tolerance=3.0)
        assert len(findings) == 1
        assert "too quiet" in findings[0].issue

    def test_critical_severity_for_extreme_deviation(self) -> None:
        """Critical severity when deviation exceeds 2x tolerance."""
        report = _make_report(lufs=-25.0)  # 11 LU from -14 target
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report, target_lufs=-14.0, tolerance=3.0)
        assert len(findings) == 1
        assert findings[0].severity == Severity.CRITICAL

    def test_major_severity_for_moderate_deviation(self) -> None:
        """Major severity for moderate deviation."""
        report = _make_report(lufs=-18.5)  # 4.5 LU from -14
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report, target_lufs=-14.0, tolerance=3.0)
        assert len(findings) == 1
        assert findings[0].severity == Severity.MAJOR

    def test_use_case_default_target(self) -> None:
        """Uses per-use-case default when no explicit target given."""
        report = _make_report(lufs=-8.0)  # Way too loud for study_focus (-18)
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report, use_case="study_focus")
        assert len(findings) == 1
        assert findings[0].evidence["target_lufs"] == -18.0

    def test_fallback_default_target(self) -> None:
        """Uses -16 LUFS default when no use_case or explicit target."""
        report = _make_report(lufs=-25.0)
        detector = LufsTargetViolationDetector()
        findings = detector.detect(report)
        assert len(findings) == 1
        assert findings[0].evidence["target_lufs"] == -16.0


# ---------------------------------------------------------------------------
# SpectralImbalanceDetector
# ---------------------------------------------------------------------------


class TestSpectralImbalance:
    def test_no_finding_when_balanced(self) -> None:
        """No finding for a reasonably balanced spectrum."""
        report = _make_report()  # default bands are balanced
        detector = SpectralImbalanceDetector()
        findings = detector.detect(report)
        assert len(findings) == 0

    def test_finding_for_dominant_band(self) -> None:
        """Finding when one band dominates > 55% of energy."""
        report = _make_report(
            band_energy={
                BandName.SUB_BASS: 0.02,
                BandName.BASS: 0.05,
                BandName.LOW_MID: 0.05,
                BandName.MID: 0.70,  # dominant
                BandName.HIGH_MID: 0.08,
                BandName.PRESENCE: 0.05,
                BandName.BRILLIANCE: 0.05,
            }
        )
        detector = SpectralImbalanceDetector()
        findings = detector.detect(report)
        assert any("dominates" in f.issue for f in findings)

    def test_finding_for_mud(self) -> None:
        """Finding when low_mid + mid > 50% with high masking."""
        report = _make_report(
            masking=0.5,
            band_energy={
                BandName.SUB_BASS: 0.02,
                BandName.BASS: 0.08,
                BandName.LOW_MID: 0.30,  # high
                BandName.MID: 0.30,  # high (combined = 60%)
                BandName.HIGH_MID: 0.15,
                BandName.PRESENCE: 0.08,
                BandName.BRILLIANCE: 0.07,
            },
        )
        detector = SpectralImbalanceDetector()
        findings = detector.detect(report)
        mud_findings = [f for f in findings if "mud" in f.issue.lower()]
        assert len(mud_findings) >= 1

    def test_no_mud_without_masking(self) -> None:
        """No mud finding if masking risk is low even with concentrated energy."""
        report = _make_report(
            masking=0.1,  # low masking
            band_energy={
                BandName.SUB_BASS: 0.02,
                BandName.BASS: 0.08,
                BandName.LOW_MID: 0.28,
                BandName.MID: 0.28,  # combined = 56% but masking is low
                BandName.HIGH_MID: 0.15,
                BandName.PRESENCE: 0.10,
                BandName.BRILLIANCE: 0.09,
            },
        )
        detector = SpectralImbalanceDetector()
        findings = detector.detect(report)
        mud_findings = [f for f in findings if "mud" in f.issue.lower()]
        assert len(mud_findings) == 0

    def test_all_findings_have_acoustic_role(self) -> None:
        """All findings from spectral imbalance have Role.ACOUSTIC."""
        report = _make_report(
            masking=0.6,
            band_energy={
                BandName.SUB_BASS: 0.01,
                BandName.BASS: 0.02,
                BandName.LOW_MID: 0.01,
                BandName.MID: 0.80,
                BandName.HIGH_MID: 0.06,
                BandName.PRESENCE: 0.05,
                BandName.BRILLIANCE: 0.05,
            },
        )
        detector = SpectralImbalanceDetector()
        findings = detector.detect(report)
        for finding in findings:
            assert finding.role == Role.ACOUSTIC


# ---------------------------------------------------------------------------
# BrightnessIntentMismatchDetector
# ---------------------------------------------------------------------------


class TestBrightnessIntentMismatch:
    def test_no_finding_when_dark_mood_dark_audio(self) -> None:
        """No mismatch when mood is dark and audio is dark."""
        report = _make_report(spectral_centroid=0.30)
        detector = BrightnessIntentMismatchDetector()
        findings = detector.detect(report, mood_keywords=["melancholic", "dark"])
        assert len(findings) == 0

    def test_finding_when_dark_mood_bright_audio(self) -> None:
        """Finding when mood is dark but audio is bright."""
        report = _make_report(spectral_centroid=0.70)
        detector = BrightnessIntentMismatchDetector()
        findings = detector.detect(report, mood_keywords=["warm", "tender"])
        assert len(findings) == 1
        assert findings[0].evidence["direction"] == "too_bright"

    def test_finding_when_bright_mood_dark_audio(self) -> None:
        """Finding when mood is bright but audio is dark."""
        report = _make_report(spectral_centroid=0.20)
        detector = BrightnessIntentMismatchDetector()
        findings = detector.detect(report, mood_keywords=["energetic", "triumphant"])
        assert len(findings) == 1
        assert findings[0].evidence["direction"] == "too_dark"

    def test_no_finding_when_bright_mood_bright_audio(self) -> None:
        """No mismatch when mood is bright and audio is bright."""
        report = _make_report(spectral_centroid=0.60)
        detector = BrightnessIntentMismatchDetector()
        findings = detector.detect(report, mood_keywords=["joyful", "playful"])
        assert len(findings) == 0

    def test_no_finding_when_no_mood_keywords(self) -> None:
        """No finding when no mood keywords match."""
        report = _make_report(spectral_centroid=0.80)
        detector = BrightnessIntentMismatchDetector()
        findings = detector.detect(report, mood_keywords=["unusual", "abstract"])
        assert len(findings) == 0

    def test_finding_has_acoustic_role(self) -> None:
        """All findings have Role.ACOUSTIC."""
        report = _make_report(spectral_centroid=0.70)
        detector = BrightnessIntentMismatchDetector()
        findings = detector.detect(report, mood_keywords=["dark"])
        assert all(f.role == Role.ACOUSTIC for f in findings)


# ---------------------------------------------------------------------------
# EnergyTrajectoryViolationDetector
# ---------------------------------------------------------------------------


class TestEnergyTrajectoryViolation:
    def test_no_finding_when_correlated(self) -> None:
        """No violation when LUFS follows tension curve."""
        # Rising tension → rising LUFS
        report = _make_report()
        report = PerceptualReport(
            lufs_integrated=-16.0,
            lufs_short_term=((0.0, -20.0), (3.0, -18.0), (6.0, -16.0), (9.0, -14.0)),
            peak_dbfs=-3.0,
            dynamic_range_db=6.0,
            spectral_centroid_mean=2000.0,
            spectral_centroid_per_section={"full": 2000.0},
            spectral_rolloff=8000.0,
            spectral_flatness=0.1,
            onset_density_per_section={"full": 3.0},
            tempo_stability_ms_drift=10.0,
            frequency_band_energy={
                BandName.SUB_BASS: 0.05,
                BandName.BASS: 0.15,
                BandName.LOW_MID: 0.20,
                BandName.MID: 0.25,
                BandName.HIGH_MID: 0.15,
                BandName.PRESENCE: 0.10,
                BandName.BRILLIANCE: 0.10,
            },
            masking_risk_score=0.1,
        )
        tension = [0.2, 0.4, 0.6, 0.8]
        detector = EnergyTrajectoryViolationDetector()
        findings = detector.detect(report, tension_values=tension)
        assert len(findings) == 0

    def test_finding_when_inversely_correlated(self) -> None:
        """Violation when LUFS goes down as tension goes up."""
        report = PerceptualReport(
            lufs_integrated=-16.0,
            lufs_short_term=((0.0, -12.0), (3.0, -14.0), (6.0, -18.0), (9.0, -22.0)),
            peak_dbfs=-3.0,
            dynamic_range_db=10.0,
            spectral_centroid_mean=2000.0,
            spectral_centroid_per_section={"full": 2000.0},
            spectral_rolloff=8000.0,
            spectral_flatness=0.1,
            onset_density_per_section={"full": 3.0},
            tempo_stability_ms_drift=10.0,
            frequency_band_energy={
                BandName.SUB_BASS: 0.05,
                BandName.BASS: 0.15,
                BandName.LOW_MID: 0.20,
                BandName.MID: 0.25,
                BandName.HIGH_MID: 0.15,
                BandName.PRESENCE: 0.10,
                BandName.BRILLIANCE: 0.10,
            },
            masking_risk_score=0.1,
        )
        tension = [0.2, 0.4, 0.6, 0.8]  # rising
        detector = EnergyTrajectoryViolationDetector()
        findings = detector.detect(report, tension_values=tension)
        assert len(findings) == 1
        assert findings[0].evidence["correlation"] < -0.2

    def test_no_finding_when_empty_data(self) -> None:
        """No finding when LUFS or tension is empty."""
        report = _make_report()
        detector = EnergyTrajectoryViolationDetector()
        findings = detector.detect(report, tension_values=[])
        assert len(findings) == 0

    def test_finding_has_acoustic_role(self) -> None:
        """All findings have Role.ACOUSTIC."""
        report = PerceptualReport(
            lufs_integrated=-16.0,
            lufs_short_term=((0.0, -12.0), (3.0, -14.0), (6.0, -18.0), (9.0, -22.0)),
            peak_dbfs=-3.0,
            dynamic_range_db=10.0,
            spectral_centroid_mean=2000.0,
            spectral_centroid_per_section={"full": 2000.0},
            spectral_rolloff=8000.0,
            spectral_flatness=0.1,
            onset_density_per_section={"full": 3.0},
            tempo_stability_ms_drift=10.0,
            frequency_band_energy={
                BandName.SUB_BASS: 0.05,
                BandName.BASS: 0.15,
                BandName.LOW_MID: 0.20,
                BandName.MID: 0.25,
                BandName.HIGH_MID: 0.15,
                BandName.PRESENCE: 0.10,
                BandName.BRILLIANCE: 0.10,
            },
            masking_risk_score=0.1,
        )
        detector = EnergyTrajectoryViolationDetector()
        findings = detector.detect(report, tension_values=[0.2, 0.4, 0.6, 0.8])
        assert all(f.role == Role.ACOUSTIC for f in findings)
