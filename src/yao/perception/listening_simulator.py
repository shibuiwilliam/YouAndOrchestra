"""Listening Simulator — Step 7.5 of the generation pipeline.

After audio rendering (Step 7), the Listening Simulator extracts a
``PerceptualReport`` and persists it as ``perceptual.json``. It also
compares the acoustic results against the intent to detect divergence.

This module orchestrates the post-render perception step. It delegates
actual feature extraction to ``AudioPerceptionAnalyzer``.

Belongs to Layer 4 (Perception Substitute).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yao.perception.audio_features import (
    AudioPerceptionAnalyzer,
    PerceptualReport,
)
from yao.schema.intent import IntentSpec

# ---------------------------------------------------------------------------
# Mood expectation mapping
# ---------------------------------------------------------------------------

# Maps intent keywords to expected acoustic characteristics.
# These are heuristic expectations for divergence detection.
_MOOD_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "calm": {"max_onset_density": 4.0, "max_dynamic_range": 8.0},
    "peaceful": {"max_onset_density": 3.0, "max_dynamic_range": 6.0},
    "relaxing": {"max_onset_density": 3.5, "max_dynamic_range": 7.0},
    "gentle": {"max_onset_density": 3.0, "max_dynamic_range": 6.0},
    "quiet": {"max_onset_density": 2.5, "max_dynamic_range": 5.0},
    "energetic": {"min_onset_density": 4.0, "min_dynamic_range": 6.0},
    "intense": {"min_onset_density": 5.0, "min_dynamic_range": 8.0},
    "aggressive": {"min_onset_density": 5.0, "min_dynamic_range": 10.0},
    "dramatic": {"min_dynamic_range": 8.0},
    "epic": {"min_dynamic_range": 10.0},
    "melancholy": {"max_spectral_centroid": 3000.0},
    "dark": {"max_spectral_centroid": 2500.0},
    "bright": {"min_spectral_centroid": 3000.0},
}


# ---------------------------------------------------------------------------
# ListeningResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ListeningResult:
    """Result of the listening simulation (Step 7.5).

    Attributes:
        report: The extracted PerceptualReport.
        mood_divergences: List of (keyword, metric, expected, actual) divergences.
        perceptual_json_path: Path where perceptual.json was saved (or None).
    """

    report: PerceptualReport
    mood_divergences: tuple[tuple[str, str, float, float], ...]
    perceptual_json_path: Path | None = None

    @property
    def has_divergence(self) -> bool:
        """Return True if any mood divergence was detected."""
        return len(self.mood_divergences) > 0


# ---------------------------------------------------------------------------
# ListeningSimulator
# ---------------------------------------------------------------------------


class ListeningSimulator:
    """Orchestrates the Listening Simulation step (Step 7.5).

    After audio is rendered, this simulator:
    1. Extracts a PerceptualReport via AudioPerceptionAnalyzer
    2. Persists it as perceptual.json in the output directory
    3. Compares acoustic features against intent mood expectations
    4. Returns a ListeningResult with any detected divergences

    Usage::

        simulator = ListeningSimulator()
        result = simulator.simulate(
            audio_path=Path("outputs/.../v001/audio.wav"),
            output_dir=Path("outputs/.../v001/"),
            intent=intent_spec,
        )
    """

    def __init__(self) -> None:
        self._analyzer = AudioPerceptionAnalyzer()

    def simulate(
        self,
        audio_path: Path,
        output_dir: Path | None = None,
        intent: IntentSpec | None = None,
        section_boundaries: dict[str, tuple[float, float]] | None = None,
    ) -> ListeningResult:
        """Run the full listening simulation pipeline.

        Args:
            audio_path: Path to rendered WAV audio.
            output_dir: Directory to save perceptual.json. If None, skip persistence.
            intent: Optional intent spec for mood divergence checking.
            section_boundaries: Optional section → (start_sec, end_sec) mapping.

        Returns:
            ListeningResult with report, divergences, and persistence path.

        Raises:
            AudioPerceptionError: If audio analysis fails.
        """
        # Step 1: Extract features
        report = self._analyzer.analyze(audio_path, section_boundaries)

        # Step 2: Persist
        json_path: Path | None = None
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / "perceptual.json"
            self._save_report(report, json_path)

        # Step 3: Check mood divergence
        divergences: list[tuple[str, str, float, float]] = []
        if intent is not None:
            divergences = self._check_mood_divergence(report, intent)

        return ListeningResult(
            report=report,
            mood_divergences=tuple(divergences),
            perceptual_json_path=json_path,
        )

    def _check_mood_divergence(
        self,
        report: PerceptualReport,
        intent: IntentSpec,
    ) -> list[tuple[str, str, float, float]]:
        """Compare report against mood expectations from intent keywords.

        Args:
            report: The acoustic analysis report.
            intent: Intent spec with keywords to check.

        Returns:
            List of (keyword, metric_name, expected_value, actual_value) tuples
            for each detected divergence.
        """
        divergences: list[tuple[str, str, float, float]] = []

        # Average onset density across sections
        densities = list(report.onset_density_per_section.values())
        avg_density = sum(densities) / max(len(densities), 1)

        for keyword in intent.keywords:
            expectations = _MOOD_EXPECTATIONS.get(keyword)
            if expectations is None:
                continue

            if "max_onset_density" in expectations:
                threshold = expectations["max_onset_density"]
                if avg_density > threshold:
                    divergences.append((keyword, "onset_density", threshold, avg_density))

            if "min_onset_density" in expectations:
                threshold = expectations["min_onset_density"]
                if avg_density < threshold:
                    divergences.append((keyword, "onset_density", threshold, avg_density))

            if "max_dynamic_range" in expectations:
                threshold = expectations["max_dynamic_range"]
                if report.dynamic_range_db > threshold:
                    divergences.append((keyword, "dynamic_range", threshold, report.dynamic_range_db))

            if "min_dynamic_range" in expectations:
                threshold = expectations["min_dynamic_range"]
                if report.dynamic_range_db < threshold:
                    divergences.append((keyword, "dynamic_range", threshold, report.dynamic_range_db))

            if "max_spectral_centroid" in expectations:
                threshold = expectations["max_spectral_centroid"]
                if report.spectral_centroid_mean > threshold:
                    divergences.append((keyword, "spectral_centroid", threshold, report.spectral_centroid_mean))

            if "min_spectral_centroid" in expectations:
                threshold = expectations["min_spectral_centroid"]
                if report.spectral_centroid_mean < threshold:
                    divergences.append((keyword, "spectral_centroid", threshold, report.spectral_centroid_mean))

        return divergences

    @staticmethod
    def _save_report(report: PerceptualReport, path: Path) -> None:
        """Serialize a PerceptualReport to JSON.

        Args:
            report: The report to save.
            path: Destination file path.
        """
        data: dict[str, Any] = {
            "lufs_integrated": report.lufs_integrated,
            "lufs_short_term": list(report.lufs_short_term),
            "peak_dbfs": report.peak_dbfs,
            "dynamic_range_db": report.dynamic_range_db,
            "spectral_centroid_mean": report.spectral_centroid_mean,
            "spectral_centroid_per_section": report.spectral_centroid_per_section,
            "spectral_rolloff": report.spectral_rolloff,
            "spectral_flatness": report.spectral_flatness,
            "onset_density_per_section": report.onset_density_per_section,
            "tempo_stability_ms_drift": report.tempo_stability_ms_drift,
            "frequency_band_energy": {band.value: energy for band, energy in report.frequency_band_energy.items()},
            "masking_risk_score": report.masking_risk_score,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
