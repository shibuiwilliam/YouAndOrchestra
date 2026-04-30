"""Rule-based generator — deterministic, theory-driven composition.

This is the MVP generator for Phase 0. It produces musically valid
compositions using simple rules: scale-based melodies, root-note bass lines,
and diatonic chord progressions. No randomness — fully deterministic for
a given spec, which enables golden tests.
"""

from __future__ import annotations

from yao.constants.instruments import INSTRUMENT_RANGES
from yao.constants.music import CHORD_INTERVALS, DYNAMICS_TO_VELOCITY
from yao.generators.base import GeneratorBase
from yao.generators.registry import register_generator
from yao.ir.notation import parse_key, scale_notes
from yao.ir.note import Note
from yao.ir.score_ir import Part, ScoreIR, Section
from yao.ir.timing import bars_to_beats
from yao.reflect.provenance import ProvenanceLog
from yao.reflect.recoverable import RecoverableDecision
from yao.schema.composition import CompositionSpec, SectionSpec
from yao.schema.trajectory import TrajectorySpec
from yao.types import BPM, Beat, MidiNote, Velocity

# Diatonic chord degrees for a major key: I, IV, V, I pattern
_MAJOR_CHORD_PATTERN: list[int] = [0, 3, 4, 0]  # scale degrees (0-indexed)
# Diatonic chord degrees for a minor key: i, iv, v, i pattern
_MINOR_CHORD_PATTERN: list[int] = [0, 3, 4, 0]

# Simple melodic rhythm patterns (in beats): mix of quarter and half notes
_MELODY_RHYTHMS: list[list[float]] = [
    [1.0, 1.0, 1.0, 1.0],  # 4 quarter notes
    [2.0, 1.0, 1.0],  # half + 2 quarters
    [1.0, 1.0, 2.0],  # 2 quarters + half
    [1.0, 0.5, 0.5, 1.0, 1.0],  # quarter, 2 eighths, 2 quarters
]


@register_generator("rule_based")
class RuleBasedGenerator(GeneratorBase):
    """Deterministic rule-based composition generator.

    Generates musically valid compositions using scale-based melodies,
    root-note bass lines, and simple diatonic chord progressions.
    All decisions are logged to provenance.
    """

    _provenance: ProvenanceLog

    def _record_recovery(
        self,
        code: str,
        severity: str,
        original: object,
        recovered: object,
        reason: str,
        impact: str,
        fix: list[str] | None = None,
    ) -> None:
        """Record a RecoverableDecision on the current provenance log."""
        decision = RecoverableDecision(
            code=code,
            severity=severity,  # type: ignore[arg-type]
            original_value=original,
            recovered_value=recovered,
            reason=reason,
            musical_impact=impact,
            suggested_fix=fix or [],
        )
        self._provenance.record_recoverable(decision)

    def generate(
        self,
        spec: CompositionSpec,
        trajectory: TrajectorySpec | None = None,
    ) -> tuple[ScoreIR, ProvenanceLog]:
        """Generate a composition from a specification.

        Args:
            spec: The composition specification.
            trajectory: Optional trajectory for dynamic shaping.

        Returns:
            Tuple of (ScoreIR, ProvenanceLog).
        """
        prov = ProvenanceLog()
        self._provenance = prov
        prov.record(
            layer="generator",
            operation="start_generation",
            parameters={"title": spec.title, "key": spec.key, "tempo": spec.tempo_bpm},
            source="RuleBasedGenerator.generate",
            rationale="Beginning rule-based composition from spec.",
        )

        root_note, scale_type = parse_key(spec.key)
        sections = self._generate_sections(
            spec=spec,
            root_note=root_note,
            scale_type=scale_type,
            trajectory=trajectory,
            provenance=prov,
        )

        score = ScoreIR(
            title=spec.title,
            tempo_bpm=spec.tempo_bpm,
            time_signature=spec.time_signature,
            key=spec.key,
            sections=tuple(sections),
        )

        prov.record(
            layer="generator",
            operation="complete_generation",
            parameters={
                "total_notes": len(score.all_notes()),
                "total_bars": score.total_bars(),
                "instruments": score.instruments(),
            },
            source="RuleBasedGenerator.generate",
            rationale="Composition generation complete.",
        )

        return score, prov

    def _generate_sections(
        self,
        *,
        spec: CompositionSpec,
        root_note: str,
        scale_type: str,
        trajectory: TrajectorySpec | None,
        provenance: ProvenanceLog,
    ) -> list[Section]:
        """Generate all sections with their parts."""
        sections: list[Section] = []
        current_bar = 0

        for section_spec in spec.sections:
            section_start = current_bar
            section_end = current_bar + section_spec.bars

            parts: list[Part] = []
            for instr_spec in spec.instruments:
                notes = self._generate_part_notes(
                    instrument=instr_spec.name,
                    role=instr_spec.role,
                    root_note=root_note,
                    scale_type=scale_type,
                    start_bar=section_start,
                    bars=section_spec.bars,
                    tempo_bpm=section_spec.tempo_bpm or spec.tempo_bpm,
                    time_signature=section_spec.time_signature or spec.time_signature,
                    section_spec=section_spec,
                    trajectory=trajectory,
                    provenance=provenance,
                )
                parts.append(Part(instrument=instr_spec.name, notes=tuple(notes)))

            sections.append(
                Section(
                    name=section_spec.name,
                    start_bar=section_start,
                    end_bar=section_end,
                    parts=tuple(parts),
                )
            )
            current_bar = section_end

        return sections

    def _generate_part_notes(
        self,
        *,
        instrument: str,
        role: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        tempo_bpm: BPM,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
        provenance: ProvenanceLog,
    ) -> list[Note]:
        """Generate notes for a single instrument part in a section."""
        if role == "melody":
            notes = self._generate_melody(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
            )
        elif role == "bass":
            notes = self._generate_bass(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
            )
        elif role == "harmony":
            notes = self._generate_chords(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
            )
        else:
            # For pad/rhythm roles, generate sustained chords as placeholder
            notes = self._generate_chords(
                instrument=instrument,
                root_note=root_note,
                scale_type=scale_type,
                start_bar=start_bar,
                bars=bars,
                time_signature=time_signature,
                section_spec=section_spec,
                trajectory=trajectory,
            )

        provenance.record(
            layer="generator",
            operation=f"generate_{role}",
            parameters={
                "instrument": instrument,
                "root": root_note,
                "scale": scale_type,
                "bars": bars,
                "note_count": len(notes),
            },
            source="RuleBasedGenerator._generate_part_notes",
            rationale=f"Generated {role} part for {instrument} using rule-based approach.",
        )

        return notes

    def _generate_melody(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
    ) -> list[Note]:
        """Generate a scale-based melody using stepwise motion."""
        octave = self._melody_octave(instrument)
        notes_in_scale = scale_notes(root_note, scale_type, octave)

        notes: list[Note] = []
        scale_idx = 0
        beats_per_bar = bars_to_beats(1, time_signature)

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            rhythm = _MELODY_RHYTHMS[bar % len(_MELODY_RHYTHMS)]
            velocity = self._compute_velocity(
                section_spec=section_spec,
                bar=start_bar + bar,
                trajectory=trajectory,
            )

            beat_offset: Beat = 0.0
            for dur in rhythm:
                if beat_offset + dur > beats_per_bar + 0.001:
                    break
                pitch = notes_in_scale[scale_idx % len(notes_in_scale)]
                note = Note(
                    pitch=pitch,
                    start_beat=bar_start + beat_offset,
                    duration_beats=dur * 0.9,  # slight gap for articulation
                    velocity=velocity,
                    instrument=instrument,
                )
                self._validate_and_clamp_note(note, instrument)
                notes.append(note)
                # Stepwise motion: move up/down the scale
                scale_idx = (scale_idx + 1) % len(notes_in_scale)
                beat_offset += dur

        return notes

    def _generate_bass(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
    ) -> list[Note]:
        """Generate a root-note bass line following the chord pattern."""
        octave = self._bass_octave(instrument)
        root_scale = scale_notes(root_note, scale_type, octave)

        notes: list[Note] = []
        chord_pattern = _MAJOR_CHORD_PATTERN if "major" in scale_type else _MINOR_CHORD_PATTERN
        beats_per_bar = bars_to_beats(1, time_signature)

        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(
                section_spec=section_spec,
                bar=start_bar + bar,
                trajectory=trajectory,
            )

            # Whole note bass (fills the bar)
            note = Note(
                pitch=pitch,
                start_beat=bar_start,
                duration_beats=beats_per_bar * 0.9,
                velocity=velocity,
                instrument=instrument,
            )
            self._validate_and_clamp_note(note, instrument)
            notes.append(note)

        return notes

    def _generate_chords(
        self,
        *,
        instrument: str,
        root_note: str,
        scale_type: str,
        start_bar: int,
        bars: int,
        time_signature: str,
        section_spec: SectionSpec,
        trajectory: TrajectorySpec | None,
    ) -> list[Note]:
        """Generate block chords following a I-IV-V-I pattern."""
        octave = self._chord_octave(instrument)
        root_scale = scale_notes(root_note, scale_type, octave)
        is_minor = "minor" in scale_type

        chord_pattern = _MINOR_CHORD_PATTERN if is_minor else _MAJOR_CHORD_PATTERN
        chord_type = "min" if is_minor else "maj"
        chord_intervals = CHORD_INTERVALS[chord_type]
        beats_per_bar = bars_to_beats(1, time_signature)

        notes: list[Note] = []
        for bar in range(bars):
            bar_start = bars_to_beats(start_bar + bar, time_signature)
            degree = chord_pattern[bar % len(chord_pattern)]
            root_pitch = root_scale[degree % len(root_scale)]
            velocity = self._compute_velocity(
                section_spec=section_spec,
                bar=start_bar + bar,
                trajectory=trajectory,
            )

            chord_vel = max(velocity - 10, 1)
            for interval in chord_intervals:
                pitch = root_pitch + interval
                if self._is_in_range(pitch, instrument):
                    note = Note(
                        pitch=pitch,
                        start_beat=bar_start,
                        duration_beats=beats_per_bar * 0.9,
                        velocity=chord_vel,
                        instrument=instrument,
                    )
                    notes.append(note)
                else:
                    self._record_recovery(
                        "CHORD_NOTE_OUT_OF_RANGE",
                        "info",
                        pitch,
                        None,
                        f"Chord note {pitch} outside {instrument} range",
                        "Chord voicing has one fewer note",
                    )

        return notes

    def _compute_velocity(
        self,
        *,
        section_spec: SectionSpec,
        bar: int,
        trajectory: TrajectorySpec | None,
    ) -> Velocity:
        """Compute velocity from dynamics marking and trajectory.

        Never hardcode velocity (CLAUDE.md failure pattern F3).
        """
        base_velocity = DYNAMICS_TO_VELOCITY.get(section_spec.dynamics, 80)

        if trajectory is not None:
            tension = trajectory.value_at("tension", bar)
            # Scale velocity: tension 0.0 → -20%, tension 1.0 → +20%
            modifier = (tension - 0.5) * 0.4
            base_velocity = int(base_velocity * (1.0 + modifier))

        clamped = max(1, min(127, base_velocity))
        if clamped != base_velocity:
            self._record_recovery(
                "VELOCITY_CLAMPED",
                "info",
                base_velocity,
                clamped,
                f"Base velocity {base_velocity} clamped to MIDI range",
                "Negligible — dynamics at MIDI boundary",
            )
        return clamped

    def _melody_octave(self, instrument: str) -> int:
        """Choose an appropriate octave for melody based on instrument range."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 5
        # Target the upper-middle of the range
        mid_note = (inst_range.midi_low + inst_range.midi_high * 2) // 3
        return (mid_note // 12) - 1

    def _bass_octave(self, instrument: str) -> int:
        """Choose an appropriate octave for bass."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 2
        low_note = inst_range.midi_low
        return (low_note // 12) - 1 + 1  # one octave above lowest

    def _chord_octave(self, instrument: str) -> int:
        """Choose an appropriate octave for chords."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 4
        mid_note = (inst_range.midi_low + inst_range.midi_high) // 2
        return (mid_note // 12) - 1

    def _is_in_range(self, pitch: MidiNote, instrument: str) -> bool:
        """Check if a pitch is within an instrument's range."""
        inst_range = INSTRUMENT_RANGES.get(instrument)
        if inst_range is None:
            return 0 <= pitch <= 127
        return inst_range.midi_low <= pitch <= inst_range.midi_high

    def _validate_and_clamp_note(self, note: Note, instrument: str) -> None:
        """Validate a note is in range. Raises RangeViolationError if not.

        Per CLAUDE.md: no silent clamping (failure pattern F2).
        """
        note.validate_range()
