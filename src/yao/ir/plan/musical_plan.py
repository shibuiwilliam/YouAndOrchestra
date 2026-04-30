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
from dataclasses import dataclass
from typing import Any

from yao.ir.plan.harmony import HarmonyPlan
from yao.ir.plan.song_form import SongFormPlan
from yao.ir.trajectory import MultiDimensionalTrajectory
from yao.reflect.provenance import ProvenanceLog
from yao.schema.intent import IntentSpec


@dataclass(frozen=True)
class MusicalPlan:
    """The integrated middle representation — Layer 3.5.

    Phase α fields (always present):
        form: Song form structure plan.
        harmony: Harmonic progression plan.
        trajectory: Multi-dimensional trajectory (control signal).
        intent: The piece's intent (human purpose).
        provenance: Append-only decision log.

    Phase β fields (None until implemented):
        motifs_phrases: Motif and phrase assignment (Phase β).
        arrangement: Arrangement/orchestration plan (Phase β).
        drums: Drum pattern plan (Phase β).
    """

    # Phase α — always present
    form: SongFormPlan
    harmony: HarmonyPlan
    trajectory: MultiDimensionalTrajectory
    intent: IntentSpec
    provenance: ProvenanceLog

    # Phase β — None until implemented
    motifs_phrases: Any = None
    arrangement: Any = None
    drums: Any = None

    def is_complete(self) -> bool:
        """Return True only when all 5 plan dimensions exist.

        In Phase α this always returns False because motifs_phrases,
        arrangement, and drums are not yet implemented.
        """
        return all([
            self.form is not None,
            self.harmony is not None,
            self.motifs_phrases is not None,
            self.arrangement is not None,
            self.drums is not None,
        ])

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
        }
        # Phase β fields — include only if present
        if self.motifs_phrases is not None:
            result["motifs_phrases"] = self.motifs_phrases
        if self.arrangement is not None:
            result["arrangement"] = self.arrangement
        if self.drums is not None:
            result["drums"] = self.drums
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
        return cls(
            form=SongFormPlan.from_dict(data["form"]),
            harmony=HarmonyPlan.from_dict(data["harmony"]),
            trajectory=trajectory or MultiDimensionalTrajectory.default(),
            intent=IntentSpec(text=data.get("intent_text", ""), keywords=[]),
            provenance=provenance or ProvenanceLog(),
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
