"""Layer 3.5: Musical Plan IR (MPIR).

The plan layer sits between Specification (Layer 1) and Score IR (Layer 3).
Plans express *why* musical decisions are made; ScoreIR expresses *what*
the concrete notes are.

Phase α implements SongFormPlan and HarmonyPlan.
Phase β will add MotifPlan, PhrasePlan, DrumPattern, ArrangementPlan.
"""

from __future__ import annotations
