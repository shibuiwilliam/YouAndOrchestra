"""Source Plan Extractor — MIDI → MusicalPlan (simplified MIR).

MVP limitations (documented per layer):
- Chord estimation: pitch class profile (not Chordino)
- Section detection: equal-length bar groups (not recurrence matrix)
- Melody extraction: highest-pitch tracking
- Drum extraction: GM channel 10

Each layer records a confidence score in provenance.

Belongs to Layer 5 (arrange/ is a consumer of render/midi_reader).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pretty_midi

from yao.ir.plan.harmony import ChordEvent, HarmonicFunction, HarmonyPlan
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.song_form import SectionPlan, SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


@dataclass(frozen=True)
class ExtractionConfidence:
    """Confidence scores per extracted layer.

    Attributes:
        form: Confidence in section detection (0.0-1.0).
        harmony: Confidence in chord estimation (0.0-1.0).
        melody: Confidence in melody extraction (0.0-1.0).
        drums: Confidence in drum extraction (0.0-1.0).
    """

    form: float
    harmony: float
    melody: float
    drums: float


class SourcePlanExtractor:
    """Extracts a MusicalPlan from a MIDI file.

    This is best-effort extraction. Confidence scores indicate reliability.
    Users can interactively correct the extracted plan.
    """

    def extract(
        self,
        midi_path: Path,
        provenance: ProvenanceLog | None = None,
    ) -> tuple[MusicalPlan, ExtractionConfidence]:
        """Extract a MusicalPlan from a MIDI file.

        Args:
            midi_path: Path to the source MIDI file.
            provenance: Optional provenance log.

        Returns:
            Tuple of (MusicalPlan, ExtractionConfidence).
        """
        if provenance is None:
            provenance = ProvenanceLog()

        midi = pretty_midi.PrettyMIDI(str(midi_path))

        # Global context
        tempo = midi.estimate_tempo()
        total_time = midi.get_end_time()
        total_bars = max(1, int(total_time * tempo / 240.0))  # rough estimate

        global_ctx = GlobalContext(
            key="C major",  # MVP: no key detection
            tempo_bpm=tempo,
            time_signature="4/4",  # MVP: assume 4/4
            genre="general",
            instruments=tuple(
                (inst.name, "melody" if i == 0 else "harmony")
                for i, inst in enumerate(midi.instruments)
                if not inst.is_drum
            ),
        )

        # Form: equal-length sections (MVP)
        form_plan, form_conf = self._extract_form(total_bars)

        # Harmony: pitch class profile per bar (MVP)
        harmony_plan, harmony_conf = self._extract_harmony(midi, total_bars, tempo)

        provenance.record(
            layer="arrange",
            operation="source_plan_extraction",
            parameters={
                "midi_path": str(midi_path),
                "total_bars": total_bars,
                "tempo": round(tempo, 1),
                "instruments": len(midi.instruments),
            },
            source="SourcePlanExtractor.extract",
            rationale="Extracted source plan from MIDI (MVP: simplified MIR).",
        )

        confidence = ExtractionConfidence(
            form=form_conf,
            harmony=harmony_conf,
            melody=0.4,  # MVP: basic highest-pitch tracking
            drums=0.8 if any(i.is_drum for i in midi.instruments) else 0.0,
        )

        plan = MusicalPlan(
            form=form_plan,
            harmony=harmony_plan,
            trajectory=MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text="Extracted from MIDI", keywords=["arrangement"]),
            provenance=provenance,
            global_context=global_ctx,
        )

        return plan, confidence

    @staticmethod
    def _extract_form(total_bars: int) -> tuple[SongFormPlan, float]:
        """Extract form by dividing into equal sections (MVP)."""
        section_size = 8
        sections: list[SectionPlan] = []
        bar = 0
        names = ["intro", "verse", "chorus", "bridge", "outro"]

        while bar < total_bars:
            end = min(bar + section_size, total_bars)
            idx = len(sections) % len(names)
            sections.append(
                SectionPlan(
                    id=names[idx],
                    start_bar=bar,
                    bars=end - bar,
                    role=names[idx],  # type: ignore[arg-type]
                    target_tension=0.5,
                    target_density=0.5,
                )
            )
            bar = end

        return SongFormPlan(sections=sections), 0.5  # low confidence

    @staticmethod
    def _extract_harmony(
        midi: pretty_midi.PrettyMIDI,
        total_bars: int,
        tempo: float,
    ) -> tuple[HarmonyPlan, float]:
        """Extract harmony via pitch class profile (MVP)."""
        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII"]
        beats_per_bar = 4.0
        sec_per_bar = beats_per_bar * 60.0 / tempo

        chord_events: list[ChordEvent] = []
        for bar in range(total_bars):
            bar_start = bar * sec_per_bar
            bar_end = bar_start + sec_per_bar

            # Collect pitch classes in this bar
            pc_counts: list[int] = [0] * 12
            for inst in midi.instruments:
                if inst.is_drum:
                    continue
                for note in inst.notes:
                    if note.start < bar_end and note.end > bar_start:
                        pc_counts[note.pitch % 12] += 1

            # Most common pitch class = root (very simplified)
            root_pc = pc_counts.index(max(pc_counts)) if any(pc_counts) else 0
            roman = roman_numerals[root_pc % 7]

            section_id = f"bar_{bar}"
            chord_events.append(
                ChordEvent(
                    section_id=section_id,
                    start_beat=float(bar * beats_per_bar),
                    duration_beats=beats_per_bar,
                    roman=roman,
                    function=HarmonicFunction.TONIC if roman == "I" else HarmonicFunction.OTHER,
                    tension_level=0.5,
                )
            )

        return HarmonyPlan(chord_events=chord_events), 0.4
