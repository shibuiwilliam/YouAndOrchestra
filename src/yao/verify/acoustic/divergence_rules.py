"""Acoustic divergence critique rules.

These rules detect problems that are invisible to symbolic evaluation:
- Symbolic-acoustic divergence (high symbolic score, low acoustic quality)
- LUFS target violations (loudness not matching production spec)
- Spectral imbalance (frequency distribution skew)

Each rule takes a PerceptualReport and optionally an EvaluationReport
for cross-modal comparison.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.perception.audio_features import BandName, PerceptualReport
from yao.verify.critique.types import Finding, Role, Severity

# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

# Default LUFS targets per use-case when production.yaml is absent.
_DEFAULT_LUFS_TARGETS: dict[str, float] = {
    "youtube_bgm": -14.0,
    "game_bgm": -16.0,
    "advertisement": -14.0,
    "study_focus": -18.0,
    "meditation": -20.0,
    "workout": -12.0,
    "cinematic": -18.0,
}

_DEFAULT_LUFS_TARGET = -16.0
_LUFS_TOLERANCE = 3.0  # ±3 LU from target


# ---------------------------------------------------------------------------
# SymbolicAcousticDivergenceDetector
# ---------------------------------------------------------------------------


class SymbolicAcousticDivergenceDetector:
    """Detect divergence between symbolic evaluation and acoustic quality.

    This rule fires when symbolic metrics indicate a strong piece (high
    pass rate) but acoustic analysis reveals problems (high masking risk,
    extreme LUFS, or poor spectral distribution).

    PROJECT.md §12.4: "When symbolic evaluation is high but acoustic
    evaluation is low, this is a critical signal."
    """

    rule_id = "acoustic.symbolic_acoustic_divergence"
    role = Role.ACOUSTIC

    def detect(
        self,
        report: PerceptualReport,
        symbolic_pass_rate: float,
        symbolic_quality_score: float,
    ) -> list[Finding]:
        """Detect symbolic-acoustic divergence.

        Args:
            report: The acoustic perception report.
            symbolic_pass_rate: Pass rate from symbolic evaluation [0, 1].
            symbolic_quality_score: Quality score from symbolic evaluation [0, 10].

        Returns:
            List of Finding objects. Empty if no divergence detected.
        """
        findings: list[Finding] = []

        # Compute a simple acoustic quality proxy score [0, 1]
        acoustic_quality = self._compute_acoustic_quality(report)

        # Divergence: symbolic is high (>0.7) but acoustic is low (<0.4)
        if symbolic_pass_rate > 0.7 and acoustic_quality < 0.4:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.CRITICAL,
                    role=self.role,
                    issue=(
                        f"Symbolic evaluation is strong ({symbolic_pass_rate:.0%} pass rate, "
                        f"quality {symbolic_quality_score:.1f}/10) but acoustic quality "
                        f"is poor ({acoustic_quality:.2f}/1.0). The symbolic layer may have "
                        f"optimized away from the listening experience."
                    ),
                    evidence={
                        "symbolic_pass_rate": symbolic_pass_rate,
                        "symbolic_quality_score": symbolic_quality_score,
                        "acoustic_quality_proxy": acoustic_quality,
                        "masking_risk": report.masking_risk_score,
                        "lufs_integrated": report.lufs_integrated,
                    },
                    recommendation={
                        "conductor": (
                            "Reduce symbolic optimization iterations and prioritize "
                            "acoustic feedback. Consider enabling audio loop."
                        ),
                    },
                )
            )

        # Also flag reverse divergence: acoustic good but symbolic bad
        if symbolic_pass_rate < 0.4 and acoustic_quality > 0.7:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"Symbolic evaluation is weak ({symbolic_pass_rate:.0%}) but "
                        f"acoustic quality is good ({acoustic_quality:.2f}). "
                        f"Symbolic rules may be overly strict or poorly calibrated."
                    ),
                    evidence={
                        "symbolic_pass_rate": symbolic_pass_rate,
                        "acoustic_quality_proxy": acoustic_quality,
                    },
                    recommendation={
                        "conductor": (
                            "Review symbolic metric thresholds — they may not align with actual listening quality."
                        ),
                    },
                )
            )

        return findings

    @staticmethod
    def _compute_acoustic_quality(report: PerceptualReport) -> float:
        """Compute a proxy acoustic quality score in [0, 1].

        Combines masking risk (lower is better), LUFS sanity,
        and spectral balance into a single quality proxy.

        Args:
            report: The perceptual report.

        Returns:
            Quality proxy in [0.0, 1.0]. Higher is better.
        """
        # Masking component: low masking = good (inverted)
        masking_score = 1.0 - report.masking_risk_score

        # LUFS sanity: not too quiet (< -40) and not clipping (> -3)
        lufs = report.lufs_integrated
        if lufs < -40.0:
            lufs_score = max(0.0, (lufs + 70.0) / 30.0)  # -70→0, -40→1
        elif lufs > -3.0:
            lufs_score = max(0.0, 1.0 - (lufs + 3.0) / 3.0)
        else:
            lufs_score = 1.0

        # Spectral balance: energy should be distributed, not all in one band
        energies = list(report.frequency_band_energy.values())
        if energies:
            max_energy = max(energies)
            # If one band has >60% of energy, penalize
            balance_score = 1.0 - max(0.0, max_energy - 0.4)
        else:
            balance_score = 0.5

        # Weighted combination
        return 0.4 * masking_score + 0.3 * lufs_score + 0.3 * balance_score


# ---------------------------------------------------------------------------
# LufsTargetViolationDetector
# ---------------------------------------------------------------------------


class LufsTargetViolationDetector:
    """Detect when the rendered audio misses the target LUFS.

    Uses the production.target_lufs from spec, or per-use-case defaults.
    """

    rule_id = "acoustic.lufs_target_violation"
    role = Role.ACOUSTIC

    def detect(
        self,
        report: PerceptualReport,
        target_lufs: float | None = None,
        use_case: str | None = None,
        tolerance: float = _LUFS_TOLERANCE,
    ) -> list[Finding]:
        """Detect LUFS target violation.

        Args:
            report: The acoustic perception report.
            target_lufs: Explicit LUFS target. If None, derived from use_case.
            use_case: Use case for default target lookup.
            tolerance: Acceptable deviation in LU.

        Returns:
            List of Finding objects.
        """
        findings: list[Finding] = []

        # Determine target
        if target_lufs is None:
            if use_case and use_case in _DEFAULT_LUFS_TARGETS:
                target_lufs = _DEFAULT_LUFS_TARGETS[use_case]
            else:
                target_lufs = _DEFAULT_LUFS_TARGET

        deviation = abs(report.lufs_integrated - target_lufs)
        if deviation > tolerance:
            direction = "too loud" if report.lufs_integrated > target_lufs else "too quiet"
            severity = Severity.CRITICAL if deviation > tolerance * 2 else Severity.MAJOR

            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=severity,
                    role=self.role,
                    issue=(
                        f"Integrated LUFS ({report.lufs_integrated:.1f}) is {direction}: "
                        f"{deviation:.1f} LU from target ({target_lufs:.1f} ± {tolerance:.1f})"
                    ),
                    evidence={
                        "lufs_integrated": report.lufs_integrated,
                        "target_lufs": target_lufs,
                        "deviation_lu": deviation,
                        "tolerance": tolerance,
                        "peak_dbfs": report.peak_dbfs,
                    },
                    recommendation={
                        "mix_engineer": (
                            f"Adjust overall gain to bring LUFS closer to {target_lufs:.1f}. "
                            f"Current peak: {report.peak_dbfs:.1f} dBFS."
                        ),
                    },
                )
            )

        return findings


# ---------------------------------------------------------------------------
# SpectralImbalanceDetector
# ---------------------------------------------------------------------------


class SpectralImbalanceDetector:
    """Detect spectral imbalance in the rendered audio.

    Fires when one frequency band dominates excessively or when the
    low-mid/mid region is over-saturated (mud).
    """

    rule_id = "acoustic.spectral_imbalance"
    role = Role.ACOUSTIC

    # Thresholds for "imbalanced"
    _DOMINANT_BAND_THRESHOLD = 0.55  # single band > 55% of total energy
    _MUD_REGION_THRESHOLD = 0.50  # low_mid + mid > 50% with masking risk

    def detect(
        self,
        report: PerceptualReport,
    ) -> list[Finding]:
        """Detect spectral imbalance.

        Args:
            report: The acoustic perception report.

        Returns:
            List of Finding objects.
        """
        findings: list[Finding] = []

        # Check for single-band dominance
        for band, energy in report.frequency_band_energy.items():
            if energy > self._DOMINANT_BAND_THRESHOLD:
                findings.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MAJOR,
                        role=self.role,
                        issue=(
                            f"Frequency band '{band.value}' dominates with "
                            f"{energy:.0%} of total energy (threshold: "
                            f"{self._DOMINANT_BAND_THRESHOLD:.0%})"
                        ),
                        evidence={
                            "dominant_band": band.value,
                            "energy_ratio": energy,
                            "threshold": self._DOMINANT_BAND_THRESHOLD,
                        },
                        recommendation={
                            "mix_engineer": (
                                f"Reduce energy in {band.value} band or add content "
                                f"in under-represented bands for better balance."
                            ),
                        },
                    )
                )

        # Check for mud (low_mid + mid saturation with high masking)
        low_mid = report.frequency_band_energy.get(BandName.LOW_MID, 0.0)
        mid = report.frequency_band_energy.get(BandName.MID, 0.0)
        mud_total = low_mid + mid

        if mud_total > self._MUD_REGION_THRESHOLD and report.masking_risk_score > 0.3:
            findings.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MAJOR,
                    role=self.role,
                    issue=(
                        f"Mud detected: low_mid + mid = {mud_total:.0%} of energy "
                        f"with masking risk {report.masking_risk_score:.2f}. "
                        f"Mix may sound congested."
                    ),
                    evidence={
                        "low_mid_energy": low_mid,
                        "mid_energy": mid,
                        "combined": mud_total,
                        "masking_risk": report.masking_risk_score,
                    },
                    recommendation={
                        "mix_engineer": (
                            "Apply surgical EQ cuts in 250-500Hz region. "
                            "Consider thinning arrangement or adjusting voicings."
                        ),
                        "orchestrator": (
                            "Spread instrument registers more widely to reduce "
                            "frequency collision in the low-mid/mid range."
                        ),
                    },
                )
            )

        return findings
