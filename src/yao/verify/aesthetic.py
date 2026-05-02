"""Aesthetic evaluation metrics — detect emotionally dead music.

Four metrics that go beyond formal correctness:
- Surprise: melodic unpredictability via bigram NLL
- Memorability: motif recurrence × identity strength
- Contrast: section-to-section style distance
- Pacing: tension arc match to planned trajectory

Based on Huron's ITPRA model. All metrics return [0, 1].

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from pathlib import Path

import yaml

from yao.ir.note import Note
from yao.ir.plan.musical_plan import MusicalPlan
from yao.ir.score_ir import ScoreIR

# ---------------------------------------------------------------------------
# Bigram model loading (reuses markov_models/)
# ---------------------------------------------------------------------------

_BIGRAM_CACHE: dict[str, dict[int, dict[int, float]]] = {}
_MODELS_DIR = Path(__file__).resolve().parent.parent / "generators" / "markov_models"


def _load_bigram_model(model_name: str = "diatonic_bigram") -> dict[int, dict[int, float]]:
    """Load a bigram transition model from YAML.

    Returns:
        dict mapping degree → {next_degree: probability}.
    """
    if model_name in _BIGRAM_CACHE:
        return _BIGRAM_CACHE[model_name]

    path = _MODELS_DIR / f"{model_name}.yaml"
    if not path.exists():
        # Fallback: uniform distribution
        uniform: dict[int, dict[int, float]] = {i: {j: 1.0 / 7 for j in range(7)} for i in range(7)}
        return uniform

    with open(path) as f:
        data = yaml.safe_load(f)

    transitions: dict[int, dict[int, float]] = {}
    for degree_str, next_probs in data.get("transitions", {}).items():
        degree = int(degree_str)
        transitions[degree] = {int(k): float(v) for k, v in next_probs.items()}

    _BIGRAM_CACHE[model_name] = transitions
    return transitions


def _pitch_to_scale_degree(pitch: int, key_root_midi: int) -> int:
    """Convert a MIDI pitch to scale degree (0-6) relative to key root."""
    # Map chromatic pitch class to nearest diatonic degree
    pc = (pitch - key_root_midi) % 12
    # Major scale intervals: 0,2,4,5,7,9,11
    major_scale = [0, 2, 4, 5, 7, 9, 11]
    # Find nearest scale degree
    min_dist = 12
    nearest_degree = 0
    for degree, interval in enumerate(major_scale):
        dist = min(abs(pc - interval), 12 - abs(pc - interval))
        if dist < min_dist:
            min_dist = dist
            nearest_degree = degree
    return nearest_degree


def _key_root_midi(key: str) -> int:
    """Get MIDI note number for key root (octave 0)."""
    note_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    root = key.split()[0].rstrip("#b")
    base = note_map.get(root, 0)
    if "#" in key.split()[0]:
        base += 1
    elif "b" in key.split()[0]:
        base -= 1
    return base


# ---------------------------------------------------------------------------
# Surprise Index
# ---------------------------------------------------------------------------


def compute_surprise_index(score: ScoreIR, plan: MusicalPlan) -> float:
    """Compute melodic surprise as average negative log probability.

    Uses the diatonic bigram model to measure how predictable the
    melody is. Higher = more surprising.

    Args:
        score: The realized score.
        plan: The musical plan (for key context).

    Returns:
        Normalized surprise index [0, 1].
    """
    notes = score.all_notes()
    if len(notes) < 2:
        return 0.0

    model = _load_bigram_model("diatonic_bigram")
    key_root = _key_root_midi(plan.global_context.key)

    surprises: list[float] = []
    for i in range(1, len(notes)):
        prev_degree = _pitch_to_scale_degree(notes[i - 1].pitch, key_root)
        curr_degree = _pitch_to_scale_degree(notes[i].pitch, key_root)

        row = model.get(prev_degree, {})
        prob = row.get(curr_degree, 1.0 / 7)  # uniform fallback
        nll = -math.log2(max(prob, 1e-9))
        surprises.append(nll)

    raw = statistics.mean(surprises) if surprises else 0.0
    # Normalize: typical range is 2.0–4.3 bits
    # Self-transition (degree 0→0) = -log2(0.05) ≈ 4.3 (maximum)
    # Stepwise (degree 0→1) = -log2(0.25) ≈ 2.0 (common/expected)
    # Midpoint ≈ 3.0 bits
    normalized = max(0.0, min(1.0, (raw - 2.0) / 2.5))
    return normalized


# ---------------------------------------------------------------------------
# Memorability Index
# ---------------------------------------------------------------------------


def compute_memorability_index(plan: MusicalPlan) -> float:
    """Compute how memorable the composition's motifs are.

    Based on: recurrence count × identity strength for each seed.
    A memorable piece has motifs that appear multiple times and are distinctive.

    Args:
        plan: The musical plan with motif data.

    Returns:
        Memorability index [0, 1].
    """
    if not plan.motif or not plan.motif.seeds:
        return 0.0

    scores: list[float] = []
    for seed in plan.motif.seeds:
        recurrence = plan.motif.recurrence_count(seed.id)
        # identity_strength is not on MotifSeed directly; use rhythm/interval uniqueness
        # Approximate identity from interval variance
        if seed.interval_shape:
            interval_variance = statistics.variance(seed.interval_shape) if len(seed.interval_shape) > 1 else 0.0
            identity = min(1.0, interval_variance / 10.0 + 0.3)
        else:
            identity = 0.3

        # Recurrence contribution: 4+ placements = full score
        recurrence_score = min(recurrence / 4.0, 1.0)
        scores.append(recurrence_score * identity)

    return statistics.mean(scores) if scores else 0.0


# ---------------------------------------------------------------------------
# Contrast Index
# ---------------------------------------------------------------------------


@dataclass
class _SectionVector:
    """Lightweight style vector for a section (for contrast computation)."""

    avg_pitch: float
    avg_velocity: float
    note_density: float  # notes per beat
    pitch_range: float  # semitones
    avg_duration: float


def _extract_section_vector(section_notes: list[Note], beats: float) -> _SectionVector:
    """Extract a style vector from a section's notes."""
    if not section_notes:
        return _SectionVector(60.0, 64.0, 0.0, 0.0, 1.0)

    pitches = [n.pitch for n in section_notes]
    velocities = [n.velocity for n in section_notes]
    durations = [n.duration_beats for n in section_notes]

    return _SectionVector(
        avg_pitch=statistics.mean(pitches),
        avg_velocity=statistics.mean(velocities),
        note_density=len(section_notes) / max(beats, 1.0),
        pitch_range=max(pitches) - min(pitches),
        avg_duration=statistics.mean(durations),
    )


def _vector_distance(a: _SectionVector, b: _SectionVector) -> float:
    """Euclidean distance between two section vectors (normalized)."""
    # Normalize each dimension to [0, 1] range
    pitch_diff = abs(a.avg_pitch - b.avg_pitch) / 24.0  # 2 octaves max
    vel_diff = abs(a.avg_velocity - b.avg_velocity) / 127.0
    density_diff = abs(a.note_density - b.note_density) / 4.0
    range_diff = abs(a.pitch_range - b.pitch_range) / 24.0
    dur_diff = abs(a.avg_duration - b.avg_duration) / 4.0

    return math.sqrt(pitch_diff**2 + vel_diff**2 + density_diff**2 + range_diff**2 + dur_diff**2) / math.sqrt(
        5.0
    )  # normalize by max possible


def compute_contrast_index(score: ScoreIR) -> float:
    """Compute contrast between adjacent sections.

    Higher = more differentiated sections.

    Args:
        score: The realized score.

    Returns:
        Contrast index [0, 1].
    """
    if len(score.sections) < 2:
        return 0.0

    vectors: list[_SectionVector] = []
    for section in score.sections:
        all_notes: list[Note] = []
        for part in section.parts:
            all_notes.extend(part.notes)
        beats = (section.end_bar - section.start_bar) * 4.0  # assume 4/4
        vectors.append(_extract_section_vector(all_notes, beats))

    distances: list[float] = []
    for i in range(len(vectors) - 1):
        distances.append(_vector_distance(vectors[i], vectors[i + 1]))

    return statistics.mean(distances) if distances else 0.0


# ---------------------------------------------------------------------------
# Pacing Index
# ---------------------------------------------------------------------------


def compute_pacing_index(score: ScoreIR, plan: MusicalPlan) -> float:
    """Compute how well the realized tension matches the planned tension.

    Compares actual velocity/density per section against the plan's
    target_tension values.

    Args:
        score: The realized score.
        plan: The musical plan with target tensions.

    Returns:
        Pacing index [0, 1] where 1.0 = perfect arc match.
    """
    if not plan.form.sections or not score.sections:
        return 0.5

    errors: list[float] = []
    for section_plan in plan.form.sections:
        target_tension = section_plan.target_tension

        # Find corresponding section in score
        score_section = None
        for ss in score.sections:
            if ss.name == section_plan.id:
                score_section = ss
                break

        if score_section is None:
            errors.append(0.5)
            continue

        # Compute actual tension from velocity
        all_notes: list[Note] = []
        for part in score_section.parts:
            all_notes.extend(part.notes)

        if not all_notes:
            errors.append(abs(target_tension - 0.0))
            continue

        # Normalize actual velocity to [0, 1] tension
        avg_velocity = statistics.mean(n.velocity for n in all_notes)
        actual_tension = (avg_velocity - 30.0) / 97.0  # 30–127 → 0–1
        actual_tension = max(0.0, min(1.0, actual_tension))

        errors.append(abs(actual_tension - target_tension))

    mean_error = statistics.mean(errors) if errors else 0.5
    return max(0.0, min(1.0, 1.0 - mean_error))


# ---------------------------------------------------------------------------
# Aggregate aesthetic score
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AestheticReport:
    """Aggregate aesthetic evaluation result."""

    surprise: float
    memorability: float
    contrast: float
    pacing: float

    @property
    def aggregate(self) -> float:
        """Weighted average of all four metrics."""
        return self.surprise * 0.25 + self.memorability * 0.25 + self.contrast * 0.25 + self.pacing * 0.25


def evaluate_aesthetics(score: ScoreIR, plan: MusicalPlan) -> AestheticReport:
    """Run all four aesthetic metrics.

    Args:
        score: The realized score.
        plan: The musical plan.

    Returns:
        AestheticReport with all four scores.
    """
    return AestheticReport(
        surprise=compute_surprise_index(score, plan),
        memorability=compute_memorability_index(plan),
        contrast=compute_contrast_index(score),
        pacing=compute_pacing_index(score, plan),
    )
