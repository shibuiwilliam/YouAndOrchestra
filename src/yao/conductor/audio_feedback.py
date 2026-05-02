"""Audio feedback — suggest adaptations from PerceptualReport analysis.

After audio rendering, this module analyzes the PerceptualReport
and suggests ScoreIR-level adaptations to improve audio quality.

Three adaptation types:
- DynamicsAdjust: scale velocities to match LUFS target
- RegisterAdjust: shift parts to reduce frequency masking
- EQAdjust: modify mix chain EQ (stretch goal)

Belongs to Layer 4 (Perception Substitute) → Layer 7 (Reflection).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.perception.audio_features import PerceptualReport


@dataclass(frozen=True)
class AudioThresholds:
    """Thresholds for audio quality evaluation.

    Attributes:
        lufs_target: Target integrated loudness in LUFS.
        lufs_tolerance: Acceptable deviation from target in LUFS.
        masking_risk_max: Maximum acceptable masking risk score [0, 1].
    """

    lufs_target: float = -16.0
    lufs_tolerance: float = 2.0
    masking_risk_max: float = 0.3


@dataclass(frozen=True)
class AudioAdaptation:
    """A suggested adaptation based on audio analysis.

    Attributes:
        type: Adaptation category ("dynamics_adjust", "register_adjust", "eq_adjust").
        parameters: Adaptation-specific parameters.
        reason: Human-readable explanation.
    """

    type: str
    parameters: dict[str, Any]
    reason: str


def suggest_audio_adaptations(
    report: PerceptualReport,
    thresholds: AudioThresholds,
) -> list[AudioAdaptation]:
    """Analyze a PerceptualReport and suggest audio adaptations.

    Args:
        report: The audio analysis report.
        thresholds: Quality thresholds to check against.

    Returns:
        List of suggested adaptations (empty if audio is acceptable).
    """
    adaptations: list[AudioAdaptation] = []

    # LUFS check: too quiet
    lufs_diff = report.lufs_integrated - thresholds.lufs_target
    if lufs_diff < -thresholds.lufs_tolerance:
        # Need to increase dynamics
        scale_factor = min(1.3, 1.0 + abs(lufs_diff) / 10.0)
        adaptations.append(
            AudioAdaptation(
                type="dynamics_adjust",
                parameters={"velocity_scale": round(scale_factor, 2), "direction": "up"},
                reason=(
                    f"LUFS {report.lufs_integrated:.1f} is below target "
                    f"{thresholds.lufs_target:.1f} (tolerance ±{thresholds.lufs_tolerance}). "
                    f"Scaling velocities by {scale_factor:.2f}."
                ),
            )
        )

    # LUFS check: too loud
    if lufs_diff > thresholds.lufs_tolerance:
        scale_factor = max(0.7, 1.0 - abs(lufs_diff) / 10.0)
        adaptations.append(
            AudioAdaptation(
                type="dynamics_adjust",
                parameters={"velocity_scale": round(scale_factor, 2), "direction": "down"},
                reason=(
                    f"LUFS {report.lufs_integrated:.1f} is above target "
                    f"{thresholds.lufs_target:.1f} (tolerance ±{thresholds.lufs_tolerance}). "
                    f"Scaling velocities by {scale_factor:.2f}."
                ),
            )
        )

    # Masking risk check
    if report.masking_risk_score > thresholds.masking_risk_max:
        adaptations.append(
            AudioAdaptation(
                type="register_adjust",
                parameters={
                    "masking_score": round(report.masking_risk_score, 3),
                    "action": "separate",
                    "octave_shift": 1,
                },
                reason=(
                    f"Masking risk {report.masking_risk_score:.2f} exceeds threshold "
                    f"{thresholds.masking_risk_max}. Separating registers."
                ),
            )
        )

    return adaptations


def apply_dynamics_adaptation(
    score: ScoreIR,
    adaptation: AudioAdaptation,
) -> ScoreIR:
    """Apply a dynamics adaptation by scaling all note velocities.

    Args:
        score: The ScoreIR to modify.
        adaptation: A dynamics_adjust adaptation with velocity_scale parameter.

    Returns:
        New ScoreIR with scaled velocities.
    """
    scale = adaptation.parameters["velocity_scale"]

    new_sections = []
    for section in score.sections:
        new_parts = []
        for part in section.parts:
            new_notes = []
            for note in part.notes:
                new_vel = max(1, min(127, round(note.velocity * scale)))
                new_notes.append(
                    Note(
                        pitch=note.pitch,
                        start_beat=note.start_beat,
                        duration_beats=note.duration_beats,
                        velocity=new_vel,
                        instrument=note.instrument,
                    )
                )
            new_parts.append(Part(instrument=part.instrument, notes=tuple(new_notes)))
        new_sections.append(
            Section(name=section.name, start_bar=section.start_bar, end_bar=section.end_bar, parts=tuple(new_parts))
        )

    return ScoreIR(
        title=score.title,
        tempo_bpm=score.tempo_bpm,
        time_signature=score.time_signature,
        key=score.key,
        sections=tuple(new_sections),
    )


def apply_register_adaptation(
    score: ScoreIR,
    adaptation: AudioAdaptation,
) -> ScoreIR:
    """Apply a register adaptation by shifting lower-register parts down.

    Identifies the part with the lowest average pitch and shifts it
    down by the specified octave shift to reduce masking.

    Args:
        score: The ScoreIR to modify.
        adaptation: A register_adjust adaptation with octave_shift parameter.

    Returns:
        New ScoreIR with adjusted registers.
    """
    octave_shift = adaptation.parameters.get("octave_shift", 1)
    semitone_shift = octave_shift * 12

    # Collect all parts across sections and find average pitches
    all_parts: list[tuple[str, float]] = []  # (instrument, avg_pitch)
    for section in score.sections:
        for part in section.parts:
            if part.notes:
                avg = sum(n.pitch for n in part.notes) / len(part.notes)
                all_parts.append((part.instrument, avg))

    if len(all_parts) < 2:  # noqa: PLR2004
        return score

    # Find the instrument with the second-highest average pitch → shift it down
    unique_instruments = list({instr for instr, _ in all_parts})
    if len(unique_instruments) < 2:  # noqa: PLR2004
        return score

    instr_avg: dict[str, list[float]] = {}
    for instr, avg in all_parts:
        instr_avg.setdefault(instr, []).append(avg)
    instr_avg_mean = {k: sum(v) / len(v) for k, v in instr_avg.items()}
    sorted_instrs = sorted(instr_avg_mean, key=lambda k: instr_avg_mean[k], reverse=True)
    shift_instrument = sorted_instrs[1]  # Second-highest

    new_sections = []
    for section in score.sections:
        new_parts = []
        for part in section.parts:
            if part.instrument == shift_instrument:
                new_notes = []
                for note in part.notes:
                    new_pitch = max(0, min(127, note.pitch - semitone_shift))
                    new_notes.append(
                        Note(
                            pitch=new_pitch,
                            start_beat=note.start_beat,
                            duration_beats=note.duration_beats,
                            velocity=note.velocity,
                            instrument=note.instrument,
                        )
                    )
                new_parts.append(Part(instrument=part.instrument, notes=tuple(new_notes)))
            else:
                new_parts.append(part)
        new_sections.append(
            Section(name=section.name, start_bar=section.start_bar, end_bar=section.end_bar, parts=tuple(new_parts))
        )

    return ScoreIR(
        title=score.title,
        tempo_bpm=score.tempo_bpm,
        time_signature=score.time_signature,
        key=score.key,
        sections=tuple(new_sections),
    )


def apply_audio_adaptations(
    score: ScoreIR,
    adaptations: list[AudioAdaptation],
) -> ScoreIR:
    """Apply all audio adaptations to a ScoreIR.

    Args:
        score: The ScoreIR to modify.
        adaptations: List of adaptations to apply.

    Returns:
        New ScoreIR with all adaptations applied.
    """
    for adaptation in adaptations:
        if adaptation.type == "dynamics_adjust":
            score = apply_dynamics_adaptation(score, adaptation)
        elif adaptation.type == "register_adjust":
            score = apply_register_adaptation(score, adaptation)
        # eq_adjust is a stretch goal — skip for now

    return score
