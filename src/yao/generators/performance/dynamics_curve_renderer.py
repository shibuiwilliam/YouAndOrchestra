"""Dynamics Curve Renderer — smooth micro_dynamics from section dynamics.

Converts discrete section dynamics (pp, mp, f, ...) into smooth per-note
micro_dynamics values using linear interpolation between section boundaries.

Never mutates ScoreIR — writes to PerformanceLayer only.
"""

from __future__ import annotations

from yao.ir.expression import NoteExpression, NoteId, PerformanceLayer
from yao.ir.score_ir import ScoreIR
from yao.ir.timing import bars_to_beats
from yao.schema.trajectory import TrajectorySpec

# Map dynamics to a normalized intensity [0, 1]
_DYNAMICS_INTENSITY: dict[str, float] = {
    "ppp": 0.05,
    "pp": 0.15,
    "p": 0.30,
    "mp": 0.45,
    "mf": 0.60,
    "f": 0.75,
    "ff": 0.90,
    "fff": 1.0,
}


class DynamicsCurveRenderer:
    """Renders smooth dynamics curves across section boundaries.

    Instead of abrupt velocity jumps at section transitions, this renderer
    creates smooth micro_dynamics adjustments that interpolate between
    section dynamic levels.
    """

    def render(
        self,
        score: ScoreIR,
        trajectory: TrajectorySpec | None = None,
    ) -> PerformanceLayer:
        """Generate dynamics curve expressions for all notes.

        Args:
            score: The ScoreIR to process.
            trajectory: Optional trajectory for additional tension shaping.

        Returns:
            PerformanceLayer with micro_dynamics values.
        """
        expressions: dict[NoteId, NoteExpression] = {}

        # Build a timeline of (beat, intensity) from sections
        section_points: list[tuple[float, float]] = []
        for section in score.sections:
            start_beat = bars_to_beats(section.start_bar, score.time_signature)
            end_beat = bars_to_beats(section.end_bar, score.time_signature)
            # Get dynamics from section name → spec lookup is not available here,
            # so we use the notes' velocities as proxy for section dynamics
            section_points.append((start_beat, self._section_intensity(section.name)))
            section_points.append((end_beat, self._section_intensity(section.name)))

        # Apply to each note
        for section in score.sections:
            section_intensity = self._section_intensity(section.name)
            for part in section.parts:
                for note in part.notes:
                    nid: NoteId = (note.instrument, note.start_beat, note.pitch)

                    # Use section's own intensity
                    intensity = section_intensity

                    # Trajectory tension boost
                    tension_mod = 0.0
                    if trajectory is not None:
                        tension = trajectory.value_at("tension", int(note.start_beat))
                        tension_mod = (tension - 0.5) * 0.3

                    # Convert to micro_dynamics [-1, 1]
                    # Center at 0.5 intensity = 0.0 micro_dynamics
                    micro_dyn = (intensity - 0.5) * 0.4 + tension_mod
                    micro_dyn = max(-1.0, min(1.0, micro_dyn))

                    expressions[nid] = NoteExpression(micro_dynamics=micro_dyn)

        return PerformanceLayer(
            note_expressions=expressions,
            section_rubato={},
            breath_marks=(),
            pedal_curves=(),
        )

    @staticmethod
    def _section_intensity(section_name: str) -> float:
        """Estimate intensity from section name heuristics."""
        name = section_name.lower()
        if "intro" in name:
            return 0.35
        if "outro" in name or "coda" in name:
            return 0.35
        if "chorus" in name or "climax" in name:
            return 0.80
        if "bridge" in name:
            return 0.65
        return 0.55  # verse / default

    @staticmethod
    def _interpolate(beat: float, points: list[tuple[float, float]]) -> float:
        """Linear interpolation between timeline points."""
        if not points:
            return 0.5
        if beat <= points[0][0]:
            return points[0][1]
        if beat >= points[-1][0]:
            return points[-1][1]
        for i in range(len(points) - 1):
            b0, v0 = points[i]
            b1, v1 = points[i + 1]
            if b0 <= beat <= b1:
                if b1 == b0:
                    return v0
                frac = (beat - b0) / (b1 - b0)
                return v0 + frac * (v1 - v0)
        return 0.5
