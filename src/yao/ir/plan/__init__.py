"""Layer 3.5: Musical Plan IR (MPIR).

The plan layer sits between Specification (Layer 1) and Score IR (Layer 3).
Plans express *why* musical decisions are made; ScoreIR expresses *what*
the concrete notes are.

Public API — import plan types from this package:

    from yao.ir.plan import MusicalPlan, GlobalContext, SongFormPlan, ...
"""

from __future__ import annotations

from yao.ir.plan.arrangement import ArrangementPlan, InstrumentAssignment, InstrumentRole
from yao.ir.plan.drums import DrumHit, DrumPattern, FillLocation, KitPiece
from yao.ir.plan.harmony import (
    CadenceRole,
    ChordEvent,
    HarmonicFunction,
    HarmonyPlan,
    ModulationEvent,
)
from yao.ir.plan.motif import MotifPlacement, MotifPlan, MotifSeed, MotifTransform
from yao.ir.plan.musical_plan import GlobalContext, MusicalPlan
from yao.ir.plan.phrase import Phrase, PhraseCadence, PhraseContour, PhrasePlan, PhraseRole
from yao.ir.plan.song_form import SectionPlan, SongFormPlan

__all__ = [
    # Core
    "MusicalPlan",
    "GlobalContext",
    # Form
    "SongFormPlan",
    "SectionPlan",
    # Harmony
    "HarmonyPlan",
    "ChordEvent",
    "HarmonicFunction",
    "CadenceRole",
    "ModulationEvent",
    # Motif
    "MotifPlan",
    "MotifSeed",
    "MotifPlacement",
    "MotifTransform",
    # Phrase
    "PhrasePlan",
    "Phrase",
    "PhraseRole",
    "PhraseContour",
    "PhraseCadence",
    # Drums
    "DrumPattern",
    "DrumHit",
    "KitPiece",
    "FillLocation",
    # Arrangement
    "ArrangementPlan",
    "InstrumentAssignment",
    "InstrumentRole",
]
