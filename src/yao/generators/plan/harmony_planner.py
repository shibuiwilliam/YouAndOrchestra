"""Rule-based harmony planner — Step 2 of the generation pipeline.

Converts CompositionSpecV2 harmony parameters + SongFormPlan into a
HarmonyPlan with chord events, cadences, and functional analysis.

Belongs to Layer 2 (Generation).
"""

from __future__ import annotations

import random
import re
import zlib
from dataclasses import replace
from typing import Any

from yao.constants.genre_profile import GenreProfile, get_genre_profile
from yao.generators.plan.base import PlanGeneratorBase, register_plan_generator
from yao.generators.thematic_recall import _section_stem
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


# Tension thresholds for chord selection behavior
_TENSION_HIGH = 0.6
_TENSION_VERY_HIGH = 0.8
_TENSION_LOW = 0.4

# Secondary dominants and borrowed chords injected at high tension.
# These are NOT in the user's palette — they're generated to satisfy Rule #7.
_SECONDARY_DOMINANTS = ["V/V", "V/vi", "V/IV"]
_BORROWED_CHORDS = ["bVII", "iv", "bVI"]


def _is_active_chord(roman: str) -> bool:
    """Check if a chord is tension-active (dominant, secondary dominant, etc.)."""
    func = _roman_to_function(roman)
    return func in (HarmonicFunction.DOMINANT, HarmonicFunction.PREDOMINANT) or "/" in roman


def _is_stable_chord(roman: str) -> bool:
    """Check if a chord is tension-stable (tonic, subdominant)."""
    func = _roman_to_function(roman)
    return func in (HarmonicFunction.TONIC, HarmonicFunction.SUBDOMINANT)


def _select_chord_by_tension(
    palette: list[str],
    position: int,
    tension: float,
) -> str:
    """Select a chord from palette, biased by tension level.

    Trajectory response (CLAUDE.md Rule #7):
    - Very high tension (>0.8): inject secondary dominants (V/V, V/vi)
      and borrowed chords (bVII, iv) even if not in palette.
    - High tension (>0.6): prefer dominant/secondary-dominant chords
      from the palette.
    - Low tension (<0.4): prefer tonic/subdominant chords.
    - Mid-range: normal palette cycling.

    Args:
        palette: Available chord symbols.
        position: Sequential position (for cycling fallback).
        tension: Current tension level [0, 1].

    Returns:
        A chord symbol from the palette (or injected tension chord).
    """
    if len(palette) <= 1:
        return palette[0]

    if tension >= _TENSION_VERY_HIGH:
        # Very high tension: inject secondary dominants and borrowed chords
        # that aren't already in the palette (Rule #7 compliance)
        extended = list(palette)
        for chord in _SECONDARY_DOMINANTS:
            if chord not in extended:
                extended.append(chord)
        for chord in _BORROWED_CHORDS:
            if chord not in extended:
                extended.append(chord)
        active = [c for c in extended if _is_active_chord(c)]
        if active:
            return active[position % len(active)]
    elif tension >= _TENSION_HIGH:
        # High tension: prefer active chords from existing palette
        active = [c for c in palette if _is_active_chord(c)]
        if active:
            return active[position % len(active)]
    elif tension <= _TENSION_LOW:
        # Low tension: prefer stable chords (tonic, subdominant)
        stable = [c for c in palette if _is_stable_chord(c)]
        if stable:
            return stable[position % len(stable)]

    # Mid-range or no matching subset: normal cycling
    return palette[position % len(palette)]


def _genre_progression(
    palette: list[str],
    n_grams: dict[tuple[str, str], float],
    length: int,
    start_roman: str,
    rng: random.Random,
) -> list[str]:
    """Genre-idiomatic roman-level progression via a first-order Markov walk.

    Walks the genre's ``progression_n_grams`` (roman → roman, so chord quality
    like ``ii7``/``Imaj7`` is preserved) starting from ``start_roman``. Where a
    chord has no outgoing transition, steps to the next palette entry (avoiding
    an immediate repeat) so the line keeps moving instead of stalling. This is
    what makes each section's harmony *flow* like the genre rather than cycling
    the flat palette identically in every section.

    Args:
        palette: The genre/spec chord palette (roman numerals with quality).
        n_grams: ``{(from_roman, to_roman): weight}`` transition table.
        length: Number of chords to produce.
        start_roman: The section's opening chord.
        rng: Seeded RNG (seed derives from the section stem for reproducibility
            and cross-section coherence).

    Returns:
        A list of roman numerals of length ``length``.
    """
    if not palette:
        return []
    transitions: dict[str, list[tuple[str, float]]] = {}
    for (frm, to), weight in n_grams.items():
        transitions.setdefault(frm, []).append((to, weight))
    seq = [start_roman if start_roman in palette else palette[0]]
    for _ in range(max(0, length - 1)):
        current = seq[-1]
        options = transitions.get(current)
        if options:
            chords, weights = zip(*options, strict=True)
            seq.append(rng.choices(list(chords), weights=list(weights), k=1)[0])
        elif current in palette and len(palette) > 1:
            seq.append(palette[(palette.index(current) + 1) % len(palette)])
        else:
            seq.append(palette[0])
    return seq


def _contrast_start_chord(palette: list[str], variant: int) -> str:
    """Choose a section's opening chord by contrast rank.

    The home material (``variant`` 0) opens on the palette's first chord (its
    tonic); each successive *distinct* section opens on a progressively more
    distant palette chord, so a bridge does not begin on the same chord the
    verse did. Same-stem returns share a variant, so they share a start.

    Args:
        palette: The chord palette.
        variant: 0 for home material, 1+ for each contrasting section.

    Returns:
        The opening roman numeral.
    """
    if not palette or variant <= 0:
        return palette[0] if palette else "I"
    step = max(1, len(palette) // 3)
    idx = (variant * step) % len(palette)
    if palette[idx] == palette[0]:
        idx = (idx + 1) % len(palette)
    return palette[idx]


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
        skill_source: str | None = None
        genre_profile: GenreProfile | None = None

        # Load genre profile for genre-specific chord preferences
        genre = spec.global_.genre.lower() if hasattr(spec.global_, "genre") else ""
        if genre:
            genre_profile = get_genre_profile(genre)

        # v3.0 Wave 2.1: Enrich palette from SkillRegistry if available
        if not palette or palette == ["I", "IV", "V", "vi"]:
            # First try GenreProfile (structured data, preferred source)
            if genre_profile and genre_profile.chord_palette:
                palette = list(genre_profile.chord_palette)
                skill_source = f"genre_profile:{genre}"
            else:
                # Fall back to SkillRegistry markdown
                from yao.skills.loader import get_skill_registry

                registry = get_skill_registry()
                skill_palette = registry.chord_palette_for(genre)
                if skill_palette:
                    palette = skill_palette
                    skill_source = genre

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

        # Section-aware harmonic variation (anti-monotony): drive each section's
        # progression from the genre's n-gram transitions, seeded by the section
        # *stem*. Distinct stems (verse vs. bridge) get distinct, contrasting
        # progressions; same-stem returns (A / A') share a seed and opening
        # chord, so their harmony matches — a coherent return, not a fourth
        # identical loop. Genres without n-grams keep the exact palette-cycling
        # behavior (no change).
        base_seed = spec.generation.seed if spec.generation.seed is not None else 42
        genre_ngrams: dict[tuple[str, str], float] = dict(genre_profile.progression_n_grams) if genre_profile else {}
        use_genre_prog = bool(genre_ngrams) and len(palette) > 1
        stem_variant: dict[str, int] = {}
        for s in spec.form.sections:
            stem = _section_stem(s.id)
            if stem not in stem_variant:
                stem_variant[stem] = len(stem_variant)

        for section_spec in spec.form.sections:
            section_id = section_spec.id
            section_bars = section_spec.bars

            # Determine chords per bar from harmonic rhythm
            chords_per_bar = _parse_chords_per_bar(spec_rhythms.get(section_id, ""))

            # Precompute this section's genre progression (if applicable).
            section_prog: list[str] | None = None
            if use_genre_prog:
                section_stem = _section_stem(section_id)
                variant = stem_variant.get(section_stem, 0)
                sec_seed = base_seed ^ (zlib.crc32(section_stem.encode()) & 0xFFFFFFFF)
                section_prog = _genre_progression(
                    palette,
                    genre_ngrams,
                    section_bars * chords_per_bar,
                    _contrast_start_chord(palette, variant),
                    random.Random(sec_seed),
                )

            for bar in range(section_bars):
                absolute_bar = current_bar + bar
                bar_beat = float(absolute_bar * beats_per_bar)
                tension = trajectory.value_at("tension", float(absolute_bar))

                for chord_idx in range(chords_per_bar):
                    chord_beat = bar_beat + chord_idx * (beats_per_bar / chords_per_bar)
                    chord_dur = beats_per_bar / chords_per_bar

                    # Pick chord: genre-idiomatic progression when available, but
                    # still honour the trajectory — climaxes inject tension chords.
                    position = bar * chords_per_bar + chord_idx
                    if section_prog is not None and position < len(section_prog) and tension < _TENSION_VERY_HIGH:
                        roman = section_prog[position]
                    else:
                        roman = _select_chord_by_tension(palette, position, tension)

                    # Determine cadence role for last chord in section
                    cadence_role = None
                    is_last_chord = bar == section_bars - 1 and chord_idx == chords_per_bar - 1
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

        # Authentic cadence for harmonic closure: end the piece on the tonic
        # (I), approached by the dominant (V) — unless the spec already set an
        # explicit cadence for the final section. Without this the final chord
        # is tension-picked and the piece rarely resolves home.
        if spec.form.sections and chord_events:
            final_section_id = spec.form.sections[-1].id
            if final_section_id not in cadences:
                final_idxs = sorted(
                    (i for i, ce in enumerate(chord_events) if ce.section_id == final_section_id),
                    key=lambda i: chord_events[i].start_beat,
                )
                if final_idxs:
                    last_i = final_idxs[-1]
                    chord_events[last_i] = replace(
                        chord_events[last_i],
                        roman="I",
                        function=HarmonicFunction.TONIC,
                        cadence_role=CadenceRole.AUTHENTIC,
                    )
                    if len(final_idxs) >= 2:  # noqa: PLR2004
                        pen_i = final_idxs[-2]
                        chord_events[pen_i] = replace(
                            chord_events[pen_i],
                            roman="V",
                            function=HarmonicFunction.DOMINANT,
                        )
                    cadences[final_section_id] = CadenceRole.AUTHENTIC

        # Descriptive half cadences: annotate (without changing chords) any
        # non-final section that already ends on a dominant-function chord as a
        # HALF cadence, so the form's cadential structure is explicit for
        # analysis/critique. Prescriptive half cadences (forcing V) need
        # phrase-period structure and are intentionally not done here.
        final_id = spec.form.sections[-1].id if spec.form.sections else None
        by_section: dict[str, list[int]] = {}
        for i, ce in enumerate(chord_events):
            by_section.setdefault(ce.section_id, []).append(i)
        for section_id, idxs in by_section.items():
            if section_id == final_id or section_id in cadences:
                continue
            last_i = max(idxs, key=lambda i: chord_events[i].start_beat)
            if chord_events[last_i].function == HarmonicFunction.DOMINANT and chord_events[last_i].cadence_role is None:
                chord_events[last_i] = replace(chord_events[last_i], cadence_role=CadenceRole.HALF)
                cadences[section_id] = CadenceRole.HALF

        # Tension resolution points: end of each section
        resolution_points = [
            float(sum(s.bars for s in spec.form.sections[: i + 1]) * beats_per_bar)
            for i in range(len(spec.form.sections))
        ]

        harmony_plan = HarmonyPlan(
            chord_events=chord_events,
            cadences=cadences,
            modulations=[],
            tension_resolution_points=resolution_points,
        )

        prov_params: dict[str, Any] = {
            "generator": "rule_based_harmony",
            "n_chord_events": len(chord_events),
            "palette": palette,
            "cadences": {k: v.value for k, v in cadences.items()},
        }
        rationale = f"Harmony plan: {len(chord_events)} chords from palette {palette}."
        if skill_source:
            prov_params["source_skill"] = skill_source
            rationale += f" Palette sourced from genre skill '{skill_source}'."

        provenance.record(
            layer="generator",
            operation="harmony_planning",
            parameters=prov_params,
            source="RuleBasedHarmonyPlanner.generate",
            rationale=rationale,
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
    match = re.search(r"(\d+)\s*chord", rhythm_desc.lower())
    if match:
        return max(1, int(match.group(1)))
    return 1
