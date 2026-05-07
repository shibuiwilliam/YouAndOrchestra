"""Layer M4: Ornament & Articulation.

Adds expressive surface to the melody: grace notes, trills, slides,
bends, articulation markings, and microtiming offsets derived from
the genre's GrooveProfile.

See PROJECT.md §3.2 (Layer M4) and IMPROVEMENT.md §4.7.
"""

from __future__ import annotations

import random

from yao.ir.melody_line import MelodyLine, MelodyNote, OrnamentedMelodyLine, OrnamentedNote
from yao.reflect.provenance import ProvenanceLog
from yao.schema.melodic_profile import MelodicProfile, OrnamentProfile

# GrooveProfile presets — timing offsets per beat position
_GROOVE_PRESETS: dict[str, dict[str, dict[float, float]]] = {
    "straight": {
        "timing": {},
        "velocity": {},
    },
    "jazz_swing": {
        "timing": {0.0: 0.0, 0.67: -8.0, 1.0: 0.0, 1.67: -8.0, 2.0: 0.0, 2.67: -8.0, 3.0: 0.0, 3.67: -8.0},
        "velocity": {0.0: 1.0, 0.67: 0.7, 1.0: 0.95, 1.67: 0.7, 2.0: 1.0, 2.67: 0.7, 3.0: 0.95, 3.67: 0.7},
    },
    "hiphop_laid_back": {
        "timing": {0.5: 5.0, 1.5: 5.0, 2.5: 5.0, 3.5: 5.0},
        "velocity": {0.0: 1.0, 0.5: 0.85, 1.0: 0.9, 1.5: 0.85, 2.0: 1.0, 2.5: 0.85, 3.0: 0.9, 3.5: 0.85},
    },
}


class OrnamentEngine:
    """Applies ornaments, articulation, and microtiming to a melody.

    This is the M4 layer — the final stage of the phrase-first pipeline
    before the melody is converted to ScoreIR.
    """

    def apply(
        self,
        melody: MelodyLine,
        profile: MelodicProfile,
        provenance: ProvenanceLog,
        *,
        rng: random.Random | None = None,
    ) -> OrnamentedMelodyLine:
        """Apply ornaments and groove to a melody line.

        Args:
            melody: The M3 output (surface-realized melody).
            profile: MelodicProfile for ornament probabilities.
            provenance: Provenance log.
            rng: Random number generator.

        Returns:
            An OrnamentedMelodyLine with expressive details.
        """
        if rng is None:
            rng = random.Random(42 + 3)

        orn_profile = profile.ornament_profile
        groove = _GROOVE_PRESETS.get(profile.groove_profile_name, _GROOVE_PRESETS["straight"])

        ornamented_notes: list[OrnamentedNote] = []
        ornament_counts: dict[str, int] = {}
        articulation_counts: dict[str, int] = {}

        for note in melody.notes:
            ornaments = self._select_ornaments(note, orn_profile, rng)
            articulation = self._select_articulation(note, orn_profile, rng)
            timing_offset = self._groove_timing(note.beat, groove)
            velocity_mod = self._groove_velocity(note.beat, groove)

            ornamented_notes.append(
                OrnamentedNote(
                    bar=note.bar,
                    beat=note.beat,
                    duration_beats=note.duration_beats,
                    midi_pitch=note.midi_pitch,
                    velocity=note.velocity,
                    note_type=note.note_type,
                    skeleton_id=note.skeleton_id,
                    ornaments=tuple(ornaments),
                    articulation=articulation,
                    micro_timing_offset_ms=timing_offset,
                    velocity_modifier=velocity_mod,
                )
            )

            for o in ornaments:
                ornament_counts[o] = ornament_counts.get(o, 0) + 1
            articulation_counts[articulation] = articulation_counts.get(articulation, 0) + 1

        result = OrnamentedMelodyLine(notes=tuple(ornamented_notes))

        provenance.record(
            layer="M4_ornament",
            operation="apply_ornaments",
            parameters={
                "input_notes": melody.note_count,
                "output_notes": result.note_count,
                "groove_profile": profile.groove_profile_name,
                "ornament_counts": ornament_counts,
                "articulation_counts": articulation_counts,
            },
            source="OrnamentEngine",
            rationale=(
                f"Applied ornaments and {profile.groove_profile_name} groove to "
                f"{melody.note_count} notes. Ornaments: {ornament_counts}. "
                f"Articulations: {articulation_counts}."
            ),
            agent="composer-subagent",
        )

        return result

    def _select_ornaments(
        self,
        note: MelodyNote,
        profile: OrnamentProfile,
        rng: random.Random,
    ) -> list[str]:
        """Select ornaments for a single note.

        Args:
            note: The melody note.
            profile: Ornament probability profile.
            rng: Random number generator.

        Returns:
            List of ornament names to apply.
        """
        ornaments: list[str] = []

        if rng.random() < profile.grace_note_probability:
            ornaments.append("grace_note")
        if rng.random() < profile.trill_probability and note.duration_beats >= 1.0:
            ornaments.append("trill")
        if rng.random() < profile.bend_probability:
            ornaments.append("bend")
        if rng.random() < profile.slide_probability:
            ornaments.append("slide")
        if rng.random() < profile.mordent_probability:
            ornaments.append("mordent")
        if rng.random() < profile.turn_probability and note.duration_beats >= 0.75:
            ornaments.append("turn")

        return ornaments

    def _select_articulation(
        self,
        note: MelodyNote,
        profile: OrnamentProfile,
        rng: random.Random,
    ) -> str:
        """Select an articulation for a note.

        Args:
            note: The melody note.
            profile: Ornament profile with articulation ratios.
            rng: Random number generator.

        Returns:
            Articulation string.
        """
        roll = rng.random()
        cumulative = 0.0

        cumulative += profile.legato_ratio
        if roll < cumulative:
            return "legato"

        cumulative += profile.staccato_ratio
        if roll < cumulative:
            return "staccato"

        cumulative += profile.accent_ratio
        if roll < cumulative:
            return "accent"

        return "normal"

    def _groove_timing(self, beat: float, groove: dict[str, dict[float, float]]) -> float:
        """Get microtiming offset from groove profile.

        Args:
            beat: Beat position within the bar.
            groove: Groove preset dictionary.

        Returns:
            Timing offset in milliseconds.
        """
        timing = groove.get("timing", {})
        if not timing:
            return 0.0

        # Find nearest beat position in the groove
        best_pos = min(timing.keys(), key=lambda k: abs(k - beat))
        if abs(best_pos - beat) < 0.2:
            return timing[best_pos]
        return 0.0

    def _groove_velocity(self, beat: float, groove: dict[str, dict[float, float]]) -> float:
        """Get velocity modifier from groove profile.

        Args:
            beat: Beat position within the bar.
            groove: Groove preset dictionary.

        Returns:
            Velocity modifier (1.0 = no change).
        """
        velocity = groove.get("velocity", {})
        if not velocity:
            return 1.0

        best_pos = min(velocity.keys(), key=lambda k: abs(k - beat))
        if abs(best_pos - beat) < 0.2:
            return velocity[best_pos]
        return 1.0
