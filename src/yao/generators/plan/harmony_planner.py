"""Rule-based harmony planner — Step 2 of the generation pipeline.

Converts CompositionSpecV2 harmony parameters + SongFormPlan into a
HarmonyPlan with chord events, cadences, and functional analysis.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

from typing import Any

from yao.generators.plan.base import PlanGeneratorBase, register_plan_generator
from yao.ir.plan.harmony import (
    CadenceRole,
    ChordEvent,
    HarmonicFunction,
    HarmonyPlan,
)
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition_v2 import CompositionSpecV2

# Map Roman numeral roots to harmonic functions
_FUNCTION_MAP: dict[str, HarmonicFunction] = {
    "I": HarmonicFunction.TONIC,
    "i": HarmonicFunction.TONIC,
    "II": HarmonicFunction.PREDOMINANT,
    "ii": HarmonicFunction.PREDOMINANT,
    "III": HarmonicFunction.TONIC,
    "iii": HarmonicFunction.TONIC,
    "IV": HarmonicFunction.SUBDOMINANT,
    "iv": HarmonicFunction.SUBDOMINANT,
    "V": HarmonicFunction.DOMINANT,
    "v": HarmonicFunction.DOMINANT,
    "VI": HarmonicFunction.SUBDOMINANT,
    "vi": HarmonicFunction.TONIC,
    "VII": HarmonicFunction.DOMINANT,
    "vii": HarmonicFunction.DOMINANT,
    "bVII": HarmonicFunction.SUBDOMINANT,
}

# Default chord progression when no palette is specified
_DEFAULT_PROGRESSION = ["I", "IV", "V", "I"]

# Cadence string → CadenceRole
_CADENCE_MAP: dict[str, CadenceRole] = {
    "half": CadenceRole.HALF,
    "authentic": CadenceRole.AUTHENTIC,
    "plagal": CadenceRole.PLAGAL,
    "deceptive": CadenceRole.DECEPTIVE,
}


def _roman_to_function(roman: str) -> HarmonicFunction:
    """Map a Roman numeral to its harmonic function."""
    # Strip modifiers like "7", "/V", etc.
    base = roman.split("/")[0].rstrip("0123456789")
    return _FUNCTION_MAP.get(base, HarmonicFunction.OTHER)


@register_plan_generator("rule_based_harmony")
class RuleBasedHarmonyPlanner(PlanGeneratorBase):
    """Deterministic harmony planner using spec chord palette and cadences."""

    def generate(
        self,
        spec: CompositionSpecV2,
        trajectory: MultiDimensionalTrajectory,
        provenance: ProvenanceLog,
    ) -> dict[str, Any]:
        """Generate a HarmonyPlan from the spec's harmony parameters.

        Requires that "form" has already been generated (needs SongFormPlan
        in the spec.form sections to determine beat positions).

        Args:
            spec: The v2 composition specification.
            trajectory: Multi-dimensional trajectory.
            provenance: Provenance log.

        Returns:
            Dict with "harmony" key containing a HarmonyPlan.
        """
        palette = list(spec.harmony.chord_palette)
        if not palette:
            palette = list(_DEFAULT_PROGRESSION)

        # Build chord events section by section
        chord_events: list[ChordEvent] = []
        cadences: dict[str, CadenceRole] = {}

        # Parse cadence assignments from spec
        spec_cadences = spec.harmony.cadence.section_cadences()
        for section_id, cadence_str in spec_cadences.items():
            if cadence_str in _CADENCE_MAP:
                cadences[section_id] = _CADENCE_MAP[cadence_str]

        # Parse harmonic rhythm from spec
        spec_rhythms = spec.harmony.harmonic_rhythm.section_rhythms()

        beats_per_bar = _parse_beats_per_bar(spec.global_.time_signature)
        current_bar = 0

        for section_spec in spec.form.sections:
            section_id = section_spec.id
            section_bars = section_spec.bars

            # Determine chords per bar from harmonic rhythm
            chords_per_bar = _parse_chords_per_bar(spec_rhythms.get(section_id, ""))

            for bar in range(section_bars):
                absolute_bar = current_bar + bar
                bar_beat = float(absolute_bar * beats_per_bar)
                tension = trajectory.value_at("tension", float(absolute_bar))

                for chord_idx in range(chords_per_bar):
                    chord_beat = bar_beat + chord_idx * (beats_per_bar / chords_per_bar)
                    chord_dur = beats_per_bar / chords_per_bar

                    # Pick chord from palette (cycle through)
                    palette_idx = (bar * chords_per_bar + chord_idx) % len(palette)
                    roman = palette[palette_idx]

                    # Determine cadence role for last chord in section
                    cadence_role = None
                    is_last_chord = (
                        bar == section_bars - 1
                        and chord_idx == chords_per_bar - 1
                    )
                    if is_last_chord and section_id in cadences:
                        cadence_role = cadences[section_id]

                    chord_events.append(
                        ChordEvent(
                            section_id=section_id,
                            start_beat=chord_beat,
                            duration_beats=chord_dur,
                            roman=roman,
                            function=_roman_to_function(roman),
                            tension_level=tension,
                            cadence_role=cadence_role,
                        )
                    )

            current_bar += section_bars

        # Tension resolution points: end of each section
        resolution_points = [
            float(sum(s.bars for s in spec.form.sections[:i + 1]) * beats_per_bar)
            for i in range(len(spec.form.sections))
        ]

        harmony_plan = HarmonyPlan(
            chord_events=chord_events,
            cadences=cadences,
            modulations=[],
            tension_resolution_points=resolution_points,
        )

        provenance.record(
            layer="generator",
            operation="harmony_planning",
            parameters={
                "generator": "rule_based_harmony",
                "n_chord_events": len(chord_events),
                "palette": palette,
                "cadences": {k: v.value for k, v in cadences.items()},
            },
            source="RuleBasedHarmonyPlanner.generate",
            rationale=f"Harmony plan: {len(chord_events)} chords from palette {palette}.",
        )

        return {"harmony": harmony_plan}


def _parse_beats_per_bar(time_signature: str) -> int:
    """Parse beats per bar from time signature string."""
    parts = time_signature.split("/")
    return int(parts[0]) if len(parts) == 2 else 4  # noqa: PLR2004


def _parse_chords_per_bar(rhythm_desc: str) -> int:
    """Parse chords per bar from a harmonic rhythm description.

    Examples:
        "1 chord per bar" → 1
        "2 chords per bar" → 2
        "" → 1 (default)
    """
    if not rhythm_desc:
        return 1
    import re

    match = re.search(r"(\d+)\s*chord", rhythm_desc.lower())
    if match:
        return max(1, int(match.group(1)))
    return 1
