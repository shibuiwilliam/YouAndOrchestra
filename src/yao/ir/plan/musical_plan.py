"""MusicalPlan — the integrated middle representation (Layer 3.5).

This is the crown jewel of v2.0: a complete pre-realization plan that
the Adversarial Critic can inspect, the multi-candidate Conductor can
rank, and the Note Realizer can faithfully execute.

Phase α: form + harmony only.
Phase β: adds motifs_phrases, arrangement, drums.

Belongs to Layer 3.5 (MPIR).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from yao.ir.conversation import ConversationPlan
from yao.ir.hook import HookPlan
from yao.ir.plan.arrangement import ArrangementPlan
from yao.ir.plan.drums import DrumPattern
from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.motif import MotifPlan
from yao.ir.plan.phrase import PhrasePlan
from yao.ir.plan.song_form import SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


@dataclass(frozen=True)
class GlobalContext:
    """Global musical parameters carried through the plan.

    These come from the specification and must be preserved through
    the entire pipeline so that note realizers can produce correct output.

    Attributes:
        key: Key signature (e.g., "G major").
        tempo_bpm: Tempo in beats per minute.
        time_signature: Time signature (e.g., "3/4").
        genre: Genre tag.
        instruments: List of (instrument_name, role) pairs.
    """

    key: str = "C major"
    tempo_bpm: float = 120.0
    time_signature: str = "4/4"
    genre: str = "general"
    instruments: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "key": self.key,
            "tempo_bpm": self.tempo_bpm,
            "time_signature": self.time_signature,
            "genre": self.genre,
            "instruments": [list(pair) for pair in self.instruments],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GlobalContext:
        """Deserialize from dict."""
        instruments = tuple(tuple(pair) for pair in data.get("instruments", []))
        return cls(
            key=data.get("key", "C major"),
            tempo_bpm=data.get("tempo_bpm", 120.0),
            time_signature=data.get("time_signature", "4/4"),
            genre=data.get("genre", "general"),
            instruments=instruments,
        )


@dataclass(frozen=True)
class MusicalPlan:
    """The integrated middle representation — Layer 3.5.

    Phase α fields (always present):
        form: Song form structure plan.
        harmony: Harmonic progression plan.
        trajectory: Multi-dimensional trajectory (control signal).
        intent: The piece's intent (human purpose).
        provenance: Append-only decision log.
        global_context: Key, tempo, time signature, instruments.

    Phase β fields (None until implemented):
        motif: Motif seeds, variations, and placements.
        phrase: Phrase structure and contour plan.
        arrangement: Per-instrument role assignments.
        drums: Drum pattern plan.
    """

    # Phase α — always present
    form: SongFormPlan
    harmony: HarmonyPlan
    trajectory: MultiDimensionalTrajectory
    intent: IntentSpec
    provenance: ProvenanceLog
    global_context: GlobalContext = field(default_factory=GlobalContext)

    # Phase β — None until implemented
    motif: MotifPlan | None = None
    phrase: PhrasePlan | None = None
    arrangement: ArrangementPlan | None = None
    drums: DrumPattern | None = None

    # Phase γ — None until implemented
    hook_plan: HookPlan | None = None
    conversation: ConversationPlan | None = None

    def is_complete(self) -> bool:
        """Return True only when all plan dimensions exist.

        In Phase α this always returns False because motif,
        arrangement, and drums are not yet populated by generators.
        """
        return all(
            [
                self.form is not None,
                self.harmony is not None,
                self.motif is not None,
                self.phrase is not None,
                self.arrangement is not None,
                self.drums is not None,
            ]
        )

    def is_phase_alpha_complete(self) -> bool:
        """Return True when the Phase α plan dimensions are present.

        This is the minimum viable plan for Phase α.
        """
        return (
            self.form is not None
            and len(self.form.sections) > 0
            and self.harmony is not None
            and len(self.harmony.chord_events) > 0
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the plan to a plain dict (for JSON persistence)."""
        result: dict[str, Any] = {
            "form": self.form.to_dict(),
            "harmony": self.harmony.to_dict(),
            "intent_text": self.intent.text,
            "global_context": self.global_context.to_dict(),
        }
        if self.motif is not None:
            result["motif"] = self.motif.to_dict()
        if self.phrase is not None:
            result["phrase"] = self.phrase.to_dict()
        if self.arrangement is not None:
            result["arrangement"] = self.arrangement.to_dict()
        if self.drums is not None:
            result["drums"] = self.drums.to_dict()
        if self.hook_plan is not None:
            result["hook_plan"] = self.hook_plan.to_dict()
        if self.conversation is not None:
            result["conversation"] = self.conversation.to_dict()
        return result

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(
        cls,
        json_str: str,
        trajectory: MultiDimensionalTrajectory | None = None,
        provenance: ProvenanceLog | None = None,
    ) -> MusicalPlan:
        """Deserialize from JSON string.

        Args:
            json_str: JSON string from to_json().
            trajectory: Trajectory to associate (not stored in JSON).
            provenance: Provenance log to associate (not stored in JSON).

        Returns:
            Reconstructed MusicalPlan.
        """
        data: dict[str, Any] = json.loads(json_str)

        motif = MotifPlan.from_dict(data["motif"]) if "motif" in data else None
        phrase = PhrasePlan.from_dict(data["phrase"]) if "phrase" in data else None
        arrangement = ArrangementPlan.from_dict(data["arrangement"]) if "arrangement" in data else None
        drums = DrumPattern.from_dict(data["drums"]) if "drums" in data else None
        hook_plan = HookPlan.from_dict(data["hook_plan"]) if "hook_plan" in data else None
        conversation = ConversationPlan.from_dict(data["conversation"]) if "conversation" in data else None
        global_ctx = GlobalContext.from_dict(data["global_context"]) if "global_context" in data else GlobalContext()

        return cls(
            form=SongFormPlan.from_dict(data["form"]),
            harmony=HarmonyPlan.from_dict(data["harmony"]),
            trajectory=trajectory or MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text=data.get("intent_text", ""), keywords=[]),
            provenance=provenance or ProvenanceLog(),
            global_context=global_ctx,
            motif=motif,
            phrase=phrase,
            arrangement=arrangement,
            drums=drums,
            hook_plan=hook_plan,
            conversation=conversation,
        )


# ---------------------------------------------------------------------------
# Type signature placeholder for the realize function (implemented in Step 7)
# ---------------------------------------------------------------------------
#
# def realize(
#     plan: MusicalPlan,
#     realizer_name: str,
#     seed: int,
#     temperature: float = 0.5,
# ) -> tuple[ScoreIR, ProvenanceLog]:
#     """Convert a MusicalPlan to concrete notes via a Note Realizer."""
#     ...
