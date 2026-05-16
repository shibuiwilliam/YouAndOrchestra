"""Project Fingerprint — cross-project style analysis and comparison.

Computes a style fingerprint for a project based on its generated output,
enabling comparison across projects and style consistency checking.

Belongs to Layer 7 (Reflection).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from yao.ir.score_ir import ScoreIR


@dataclass(frozen=True)
class ProjectFingerprint:
    """Style fingerprint summarizing a project's musical characteristics.

    Attributes:
        project_id: Project identifier.
        genre: Primary genre of the project.
        avg_tempo: Average tempo across iterations.
        avg_density: Average note density (notes per bar).
        avg_velocity: Average velocity.
        velocity_range: Dynamic range (max - min velocity).
        pitch_center: Average MIDI pitch.
        pitch_spread: Standard deviation of pitches.
        leap_ratio: Ratio of melodic intervals > 2 semitones.
        swing_indicator: Timing deviation from grid.
        iteration_count: Number of iterations analyzed.
    """

    project_id: str
    genre: str = "general"
    avg_tempo: float = 120.0
    avg_density: float = 0.0
    avg_velocity: float = 80.0
    velocity_range: float = 0.0
    pitch_center: float = 60.0
    pitch_spread: float = 0.0
    leap_ratio: float = 0.0
    swing_indicator: float = 0.0
    iteration_count: int = 0


def compute_fingerprint(
    project_id: str,
    scores: list[ScoreIR],
    genre: str = "general",
) -> ProjectFingerprint:
    """Compute a style fingerprint from a list of generated scores.

    Args:
        project_id: Project identifier.
        scores: Generated ScoreIR instances to analyze.
        genre: Primary genre.

    Returns:
        ProjectFingerprint summarizing the project's style.
    """
    if not scores:
        return ProjectFingerprint(project_id=project_id, genre=genre)

    all_tempos: list[float] = []
    all_densities: list[float] = []
    all_velocities: list[int] = []
    all_pitches: list[int] = []
    all_leaps: list[float] = []
    all_swing: list[float] = []

    for score in scores:
        notes = score.all_notes()
        if not notes:
            continue

        tempo = score.tempo_bpm if hasattr(score, "tempo_bpm") else 120.0
        all_tempos.append(tempo)

        total_bars = max(score.total_bars(), 1)
        all_densities.append(len(notes) / total_bars)

        velocities = [n.velocity for n in notes]
        all_velocities.extend(velocities)

        pitches = [n.pitch for n in notes]
        all_pitches.extend(pitches)

        # Leap ratio
        leaps = sum(1 for i in range(1, len(notes)) if abs(notes[i].pitch - notes[i - 1].pitch) > 2)
        all_leaps.append(leaps / max(len(notes) - 1, 1))

        # Swing indicator
        fracs = [n.start_beat % 1.0 for n in notes]
        if fracs:
            avg_frac = sum(fracs) / len(fracs)
            swing = (sum((f - avg_frac) ** 2 for f in fracs) / len(fracs)) ** 0.5
            all_swing.append(swing)

    if not all_velocities:
        return ProjectFingerprint(project_id=project_id, genre=genre)

    avg_pitch = sum(all_pitches) / len(all_pitches)
    pitch_spread = (sum((p - avg_pitch) ** 2 for p in all_pitches) / len(all_pitches)) ** 0.5

    return ProjectFingerprint(
        project_id=project_id,
        genre=genre,
        avg_tempo=sum(all_tempos) / len(all_tempos) if all_tempos else 120.0,
        avg_density=sum(all_densities) / len(all_densities) if all_densities else 0.0,
        avg_velocity=sum(all_velocities) / len(all_velocities),
        velocity_range=max(all_velocities) - min(all_velocities),
        pitch_center=avg_pitch,
        pitch_spread=round(pitch_spread, 2),
        leap_ratio=sum(all_leaps) / len(all_leaps) if all_leaps else 0.0,
        swing_indicator=sum(all_swing) / len(all_swing) if all_swing else 0.0,
        iteration_count=len(scores),
    )


def fingerprint_distance(a: ProjectFingerprint, b: ProjectFingerprint) -> float:
    """Euclidean distance between two project fingerprints.

    Normalized so that each dimension contributes roughly equally.

    Args:
        a: First fingerprint.
        b: Second fingerprint.

    Returns:
        Distance (0.0 = identical style).
    """
    return math.sqrt(
        ((a.avg_tempo - b.avg_tempo) / 100.0) ** 2
        + ((a.avg_density - b.avg_density) / 20.0) ** 2
        + ((a.avg_velocity - b.avg_velocity) / 127.0) ** 2
        + ((a.velocity_range - b.velocity_range) / 127.0) ** 2
        + ((a.pitch_center - b.pitch_center) / 127.0) ** 2
        + ((a.pitch_spread - b.pitch_spread) / 30.0) ** 2
        + (a.leap_ratio - b.leap_ratio) ** 2
        + (a.swing_indicator - b.swing_indicator) ** 2
    )


def save_fingerprint(fp: ProjectFingerprint, path: Path) -> None:
    """Save a project fingerprint to JSON.

    Args:
        fp: The fingerprint to save.
        path: Output path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "project_id": fp.project_id,
        "genre": fp.genre,
        "avg_tempo": fp.avg_tempo,
        "avg_density": fp.avg_density,
        "avg_velocity": fp.avg_velocity,
        "velocity_range": fp.velocity_range,
        "pitch_center": fp.pitch_center,
        "pitch_spread": fp.pitch_spread,
        "leap_ratio": fp.leap_ratio,
        "swing_indicator": fp.swing_indicator,
        "iteration_count": fp.iteration_count,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_fingerprint(path: Path) -> ProjectFingerprint:
    """Load a project fingerprint from JSON.

    Args:
        path: Path to fingerprint JSON.

    Returns:
        ProjectFingerprint.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    return ProjectFingerprint(**data)
