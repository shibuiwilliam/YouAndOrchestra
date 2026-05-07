"""PhraseAwareGenerator — the four-layer phrase-first melody generator.

Orchestrates M1 → M2 → M3 → M4 in strict order, producing a complete
ScoreIR with full provenance. Registered alongside existing generators
via @register_generator("phrase_aware").

See PROJECT.md §3.2 and CLAUDE.md §Phase 2.
"""

from __future__ import annotations

import random

from yao.generators.base import GeneratorBase
from yao.generators.melody.motif_developer import MotifDevelopmentPlanner
from yao.generators.melody.ornament import OrnamentEngine
from yao.generators.melody.skeleton import SkeletonGenerator
from yao.generators.melody.surface import SurfaceRealizer
from yao.generators.registry import register_generator
from yao.ir.melody_line import OrnamentedMelodyLine
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.schema.composition import CompositionSpec
from yao.schema.melodic_profile import MelodicProfile, load_melodic_profile
from yao.schema.trajectory import TrajectorySpec


@register_generator("phrase_aware")
class PhraseAwareGenerator(GeneratorBase):
    """Four-layer phrase-first melody generator.

    Generates melodies through a structured pipeline:
    1. M1 (MotifDevelopmentPlanner): Plan phrase structure and motifs
    2. M2 (SkeletonGenerator): Generate chord-tone skeleton
    3. M3 (SurfaceRealizer): Fill surface with passing/neighbor tones
    4. M4 (OrnamentEngine): Add ornaments, articulation, microtiming

    The existing rule_based and stochastic generators are NOT affected.
    Users opt in via ``generation.strategy: phrase_aware`` in their spec.
    """

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a composition using the phrase-first pipeline.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory specification (reserved for future use).

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        provenance = ProvenanceLog()

        # Load the genre's MelodicProfile
        profile = self._load_profile(spec)

        # Seed for reproducibility
        seed = spec.generation.seed if spec.generation.seed is not None else 42
        rng = random.Random(seed)

        # M1: Phrase & Motif Plan
        planner = MotifDevelopmentPlanner()
        phrase_plan = planner.plan(spec, profile, provenance, rng=rng)

        # M2: Skeleton Generation
        skeleton_gen = SkeletonGenerator()
        skeleton = skeleton_gen.generate(
            phrase_plan,
            spec,
            profile,
            provenance,
            rng=random.Random(seed + 1),
        )

        # M3: Surface Realization
        surface_realizer = SurfaceRealizer()
        melody_line = surface_realizer.realize(
            skeleton,
            spec,
            profile,
            provenance,
            rng=random.Random(seed + 2),
        )

        # M4: Ornament & Articulation
        ornament_engine = OrnamentEngine()
        ornamented = ornament_engine.apply(
            melody_line,
            profile,
            provenance,
            rng=random.Random(seed + 3),
        )

        # Convert to ScoreIR
        score = self._to_score_ir(ornamented, spec)

        # Record overall provenance
        provenance.record(
            layer="generator",
            operation="phrase_aware_generate",
            parameters={
                "genre": profile.genre,
                "strategy": "phrase_aware",
                "seed": seed,
                "total_bars": sum(s.bars for s in spec.sections),
                "phrase_count": phrase_plan.phrase_count,
                "skeleton_notes": skeleton.note_count,
                "surface_notes": melody_line.note_count,
                "final_notes": ornamented.note_count,
            },
            source="PhraseAwareGenerator",
            rationale=(
                f"Generated {profile.genre} piece via phrase-first pipeline: "
                f"{phrase_plan.phrase_count} phrases → {skeleton.note_count} skeleton → "
                f"{melody_line.note_count} surface → {ornamented.note_count} ornamented."
            ),
            agent="composer-subagent",
        )

        return score, provenance

    def _load_profile(self, spec: CompositionSpec) -> MelodicProfile:
        """Load the MelodicProfile for the spec's genre.

        Falls back to a minimal default if the genre doesn't have a profile.

        Args:
            spec: Composition specification.

        Returns:
            A MelodicProfile.
        """
        from yao.schema.melodic_profile import IntervalDistribution, PhraseLengthDistribution

        try:
            return load_melodic_profile(spec.genre)
        except Exception:
            # Fallback to a generic profile for genres without profiles
            return MelodicProfile(
                genre=spec.genre,
                description="Generic fallback profile",
                interval_distribution=IntervalDistribution(
                    distribution={0: 0.05, 1: 0.10, 2: 0.30, 3: 0.20, 4: 0.15, 5: 0.10, 7: 0.10}
                ),
                phrase_length_distribution=PhraseLengthDistribution(distribution={4: 0.40, 8: 0.50, 16: 0.10}),
            )

    def _to_score_ir(self, ornamented: OrnamentedMelodyLine, spec: CompositionSpec) -> ScoreIR:
        """Convert an OrnamentedMelodyLine to ScoreIR.

        Args:
            ornamented: The M4 output.
            spec: Composition specification.

        Returns:
            A complete ScoreIR.
        """
        # Find the melody instrument
        melody_instrument = "piano"
        for inst in spec.instruments:
            if inst.role == "melody":
                melody_instrument = inst.name
                break

        # Build sections
        sections: list[Section] = []
        current_bar = 0

        for section_spec in spec.sections:
            section_start = current_bar
            section_end = current_bar + section_spec.bars

            # Collect notes for this section
            section_notes: list[Note] = []
            for onote in ornamented.notes:
                if section_start <= onote.bar < section_end:
                    # Convert beat position to absolute beat
                    abs_beat = bars_to_beats(onote.bar, spec.time_signature) + onote.beat

                    section_notes.append(
                        Note(
                            pitch=onote.midi_pitch,
                            start_beat=abs_beat,
                            duration_beats=onote.duration_beats,
                            velocity=onote.effective_velocity,
                            instrument=melody_instrument,
                            articulation=onote.articulation if onote.articulation != "normal" else None,
                            microtiming_offset_ms=onote.micro_timing_offset_ms,
                        )
                    )

            parts = (Part(instrument=melody_instrument, notes=tuple(section_notes)),)

            sections.append(
                Section(
                    name=section_spec.name,
                    start_bar=section_start,
                    end_bar=section_end,
                    parts=parts,
                )
            )

            current_bar = section_end

        return ScoreIR(
            title=spec.title,
            tempo_bpm=spec.tempo_bpm,
            time_signature=spec.time_signature,
            key=spec.key,
            sections=tuple(sections),
        )
