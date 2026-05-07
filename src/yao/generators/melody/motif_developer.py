"""Layer M1: Phrase & Motif Planner.

Defines the logical structure of the melody before any pitches are chosen.
Determines phrase boundaries, assigns functions and cadences, generates
germ motifs, and plans motif transformations across phrases.

See PROJECT.md §3.2 (Layer M1) and IMPROVEMENT.md §4.1.
"""

from __future__ import annotations

import random

from yao.constants.music import SCALE_INTERVALS
from yao.ir.motif import Motif
from yao.ir.notation import note_name_to_midi
from yao.ir.note import Note
from yao.ir.phrase import CadenceType, Phrase, PhraseFunction, PhrasePlan
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.melodic_profile import MelodicProfile

# Mapping from phrase function to typical cadence types
_FUNCTION_CADENCE_MAP: dict[PhraseFunction, list[tuple[CadenceType, float]]] = {
    PhraseFunction.STATEMENT: [(CadenceType.HALF, 0.6), (CadenceType.NONE, 0.4)],
    PhraseFunction.QUESTION: [(CadenceType.HALF, 0.7), (CadenceType.DECEPTIVE, 0.3)],
    PhraseFunction.ANSWER: [(CadenceType.AUTHENTIC, 0.7), (CadenceType.PLAGAL, 0.3)],
    PhraseFunction.DEVELOPMENT: [(CadenceType.HALF, 0.4), (CadenceType.DECEPTIVE, 0.3), (CadenceType.NONE, 0.3)],
    PhraseFunction.RECAPITULATION: [(CadenceType.AUTHENTIC, 0.8), (CadenceType.PLAGAL, 0.2)],
    PhraseFunction.CODA: [(CadenceType.AUTHENTIC, 0.5), (CadenceType.PLAGAL, 0.5)],
}

# Function sequences for typical section types
_SECTION_FUNCTION_PATTERNS: dict[int, list[list[PhraseFunction]]] = {
    2: [[PhraseFunction.STATEMENT, PhraseFunction.ANSWER]],
    3: [[PhraseFunction.STATEMENT, PhraseFunction.QUESTION, PhraseFunction.ANSWER]],
    4: [
        [PhraseFunction.STATEMENT, PhraseFunction.QUESTION, PhraseFunction.STATEMENT, PhraseFunction.ANSWER],
        [PhraseFunction.STATEMENT, PhraseFunction.DEVELOPMENT, PhraseFunction.RECAPITULATION, PhraseFunction.ANSWER],
    ],
}

# Contour archetypes
_CONTOUR_ARCHETYPES = ["arch", "descending", "ascending", "wave"]


class MotifDevelopmentPlanner:
    """Plans phrase structure and motif assignments for a section or piece.

    This is the M1 layer of the phrase-first pipeline. Its output
    (PhrasePlan) drives all subsequent layers.
    """

    def plan(
        self,
        spec: CompositionSpec,
        profile: MelodicProfile,
        provenance: ProvenanceLog,
        *,
        rng: random.Random | None = None,
    ) -> PhrasePlan:
        """Generate a complete phrase plan for the composition.

        Args:
            spec: The composition specification.
            profile: The active MelodicProfile for genre parameterization.
            provenance: Provenance log to record decisions.
            rng: Random number generator for reproducibility.

        Returns:
            A PhrasePlan covering all sections in the spec.
        """
        if rng is None:
            seed = spec.generation.seed if spec.generation.seed is not None else 42
            rng = random.Random(seed)

        motif_library = self._generate_motifs(spec, profile, rng)
        phrases = self._plan_phrases(spec, profile, motif_library, rng)

        plan = PhrasePlan(phrases=tuple(phrases), motif_library=motif_library)

        provenance.record(
            layer="M1_phrase_plan",
            operation="plan_phrases",
            parameters={
                "genre": profile.genre,
                "total_bars": sum(s.bars for s in spec.sections),
                "phrase_count": len(phrases),
                "motif_count": len(motif_library),
            },
            source="MotifDevelopmentPlanner",
            rationale=(
                f"Planned {len(phrases)} phrases across {len(spec.sections)} sections "
                f"using {profile.genre} profile. Motif length={profile.motif_length_bars} bars, "
                f"recurrence_rate={profile.motif_recurrence_rate}."
            ),
            agent="composer-subagent",
        )

        return plan

    def _generate_motifs(
        self,
        spec: CompositionSpec,
        profile: MelodicProfile,
        rng: random.Random,
    ) -> dict[str, Motif]:
        """Generate germ motifs for the piece.

        Args:
            spec: Composition specification.
            profile: MelodicProfile for genre-aware motif generation.
            rng: Random number generator.

        Returns:
            Dictionary mapping motif IDs to Motif objects.
        """
        key_parts = spec.key.split()
        root_name = key_parts[0] if key_parts else "C"
        scale_type = key_parts[1] if len(key_parts) > 1 else "major"

        root_midi = note_name_to_midi(f"{root_name}4")
        intervals = list(SCALE_INTERVALS.get(scale_type, SCALE_INTERVALS["major"]))

        motifs: dict[str, Motif] = {}

        # Primary motif
        primary_notes = self._generate_motif_notes(
            root_midi,
            intervals,
            profile,
            rng,
            label="primary",
        )
        motifs["primary"] = Motif(notes=tuple(primary_notes), label="primary")

        # Secondary motif (contrasting)
        secondary_notes = self._generate_motif_notes(
            root_midi,
            intervals,
            profile,
            rng,
            label="secondary",
            start_degree_offset=2,
        )
        motifs["secondary"] = Motif(notes=tuple(secondary_notes), label="secondary")

        return motifs

    def _generate_motif_notes(
        self,
        root_midi: int,
        intervals: list[int],
        profile: MelodicProfile,
        rng: random.Random,
        *,
        label: str,
        start_degree_offset: int = 0,
    ) -> list[Note]:
        """Generate notes for a single motif.

        Args:
            root_midi: MIDI note number of the key root.
            intervals: Scale intervals in semitones.
            profile: MelodicProfile for parameterization.
            rng: Random number generator.
            label: Motif label.
            start_degree_offset: Offset in scale degrees for the starting pitch.

        Returns:
            List of Note objects forming the motif.
        """
        # Determine number of notes based on motif length
        beats_per_bar = 4.0
        motif_beats = profile.motif_length_bars * beats_per_bar
        note_count = max(3, min(8, int(motif_beats * 2)))

        # Build pitch candidates from the scale
        scale_pitches = [root_midi + iv for iv in intervals]
        # Add octave above
        scale_pitches.extend(root_midi + 12 + iv for iv in intervals)

        # Weight by interval distribution
        dist = profile.interval_distribution.normalized()

        # Generate notes
        notes: list[Note] = []
        start_idx = start_degree_offset % len(intervals)
        current_pitch = root_midi + intervals[start_idx]
        beat = 0.0
        dur = motif_beats / note_count

        for i in range(note_count):
            notes.append(
                Note(
                    pitch=current_pitch,
                    start_beat=beat,
                    duration_beats=dur,
                    velocity=80,
                    instrument="melody",
                )
            )
            beat += dur

            # Select next pitch using interval distribution
            if i < note_count - 1:
                current_pitch = self._select_next_pitch(
                    current_pitch,
                    scale_pitches,
                    dist,
                    rng,
                )

        return notes

    def _select_next_pitch(
        self,
        current: int,
        scale_pitches: list[int],
        interval_dist: dict[int, float],
        rng: random.Random,
    ) -> int:
        """Select the next pitch using the genre's interval distribution.

        Args:
            current: Current MIDI pitch.
            scale_pitches: Available scale pitches.
            interval_dist: Normalized interval distribution.
            rng: Random number generator.

        Returns:
            Next MIDI pitch.
        """
        candidates: list[tuple[int, float]] = []
        for pitch in scale_pitches:
            interval = abs(pitch - current)
            weight = interval_dist.get(interval, 0.01)
            if pitch != current or interval_dist.get(0, 0) > 0:
                candidates.append((pitch, weight))

        if not candidates:
            return current

        pitches, weights = zip(*candidates, strict=False)
        total = sum(weights)
        if total <= 0:
            return int(rng.choice(pitches))

        return int(rng.choices(pitches, weights=weights, k=1)[0])

    def _plan_phrases(
        self,
        spec: CompositionSpec,
        profile: MelodicProfile,
        motif_library: dict[str, Motif],
        rng: random.Random,
    ) -> list[Phrase]:
        """Plan phrases across all sections.

        Args:
            spec: Composition specification.
            profile: MelodicProfile for phrase length preferences.
            motif_library: Available motifs.
            rng: Random number generator.

        Returns:
            List of Phrase objects covering all bars.
        """
        phrases: list[Phrase] = []
        current_bar = 0

        for section in spec.sections:
            section_phrases = self._plan_section_phrases(
                section_bars=section.bars,
                start_bar=current_bar,
                profile=profile,
                motif_library=motif_library,
                rng=rng,
            )
            phrases.extend(section_phrases)
            current_bar += section.bars

        return phrases

    def _plan_section_phrases(
        self,
        section_bars: int,
        start_bar: int,
        profile: MelodicProfile,
        motif_library: dict[str, Motif],
        rng: random.Random,
    ) -> list[Phrase]:
        """Plan phrases for a single section.

        Args:
            section_bars: Number of bars in the section.
            start_bar: Starting bar offset.
            profile: MelodicProfile for phrase preferences.
            motif_library: Available motifs.
            rng: Random number generator.

        Returns:
            List of Phrase objects for this section.
        """
        # Determine phrase boundaries
        phrase_lengths = self._select_phrase_lengths(section_bars, profile, rng)

        # Determine function sequence
        functions = self._select_functions(len(phrase_lengths), rng)

        # Build phrases
        phrases: list[Phrase] = []
        bar = start_bar
        motif_ids = list(motif_library.keys())
        transformations = list(profile.motif_transformations.keys()) or ["identity"]
        transform_weights = list(profile.motif_transformations.values()) or [1.0]

        for _i, (length, function) in enumerate(zip(phrase_lengths, functions, strict=False)):
            cadence = self._select_cadence(function, rng)

            # Assign motif based on function
            motif_id: str | None
            if function in (PhraseFunction.STATEMENT, PhraseFunction.RECAPITULATION):
                motif_id = "primary"
            elif function == PhraseFunction.QUESTION:
                motif_id = "secondary" if "secondary" in motif_ids else "primary"
            else:
                motif_id = rng.choice(motif_ids) if motif_ids else None

            # Select transformation
            transformation = (
                rng.choices(transformations, weights=transform_weights, k=1)[0] if transformations else "identity"
            )

            # Select contour
            contour = rng.choice(_CONTOUR_ARCHETYPES)

            phrases.append(
                Phrase(
                    start_bar=bar,
                    end_bar=bar + length,
                    function=function,
                    cadence=cadence,
                    motif_id=motif_id,
                    motif_transformation=transformation,
                    contour_archetype=contour,
                )
            )
            bar += length

        return phrases

    def _select_phrase_lengths(
        self,
        total_bars: int,
        profile: MelodicProfile,
        rng: random.Random,
    ) -> list[int]:
        """Select phrase lengths that sum to total_bars.

        Args:
            total_bars: Total bars to fill.
            profile: Profile with phrase length distribution.
            rng: Random number generator.

        Returns:
            List of phrase lengths summing to total_bars.
        """
        dist = profile.phrase_length_distribution.normalized()
        available_lengths = sorted(dist.keys())
        weights = [dist[k] for k in available_lengths]

        if not available_lengths:
            available_lengths = [4]
            weights = [1.0]

        lengths: list[int] = []
        remaining = total_bars

        while remaining > 0:
            # Filter lengths that don't exceed remaining
            valid = [(ln, w) for ln, w in zip(available_lengths, weights, strict=False) if ln <= remaining]
            if not valid:
                # If no valid length fits, use what's left
                lengths.append(remaining)
                break

            valid_lengths, valid_weights = zip(*valid, strict=False)
            chosen = rng.choices(valid_lengths, weights=valid_weights, k=1)[0]
            lengths.append(chosen)
            remaining -= chosen

        return lengths

    def _select_functions(
        self,
        phrase_count: int,
        rng: random.Random,
    ) -> list[PhraseFunction]:
        """Select a function sequence for the given number of phrases.

        Args:
            phrase_count: Number of phrases to assign functions to.
            rng: Random number generator.

        Returns:
            List of PhraseFunction values.
        """
        if phrase_count <= 0:
            return []

        # Try to use a predefined pattern
        patterns = _SECTION_FUNCTION_PATTERNS.get(phrase_count)
        if patterns:
            return list(rng.choice(patterns))

        # For other counts, build a reasonable sequence
        functions: list[PhraseFunction] = []
        for i in range(phrase_count):
            if i == 0:
                functions.append(PhraseFunction.STATEMENT)
            elif i == phrase_count - 1:
                functions.append(PhraseFunction.ANSWER)
            elif i == phrase_count - 2:
                functions.append(PhraseFunction.RECAPITULATION if phrase_count > 4 else PhraseFunction.STATEMENT)
            else:
                functions.append(rng.choice([PhraseFunction.QUESTION, PhraseFunction.DEVELOPMENT]))

        return functions

    def _select_cadence(
        self,
        function: PhraseFunction,
        rng: random.Random,
    ) -> CadenceType:
        """Select a cadence type appropriate for the phrase function.

        Args:
            function: The phrase function.
            rng: Random number generator.

        Returns:
            Appropriate CadenceType.
        """
        options = _FUNCTION_CADENCE_MAP.get(function, [(CadenceType.HALF, 1.0)])
        cadences, weights = zip(*options, strict=False)
        result: CadenceType = rng.choices(cadences, weights=weights, k=1)[0]
        return result
