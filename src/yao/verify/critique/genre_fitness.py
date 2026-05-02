"""Genre fitness critique rules — detect genre convention violations.

Rules:
- TempoOutOfRangeDetector: tempo outside typical genre range
- InstrumentMismatchDetector: instruments not typical for genre

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity

# Simplified genre tempo ranges
_GENRE_TEMPO: dict[str, tuple[float, float]] = {
    "cinematic": (60, 160),
    "jazz": (80, 220),
    "rock": (100, 150),
    "pop": (90, 140),
    "edm": (120, 140),
    "classical": (40, 160),
    "ambient": (60, 100),
}


class TempoOutOfRangeDetector(CritiqueRule):
    """Detect tempo outside typical genre range."""

    rule_id = "tempo_out_of_range"
    role = Role.ARRANGEMENT

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check tempo against genre conventions."""
        genre = plan.global_context.genre.lower()
        tempo = plan.global_context.tempo_bpm

        for genre_key, (lo, hi) in _GENRE_TEMPO.items():
            if genre_key in genre:
                if tempo < lo or tempo > hi:
                    return [
                        Finding(
                            rule_id=self.rule_id,
                            severity=Severity.MINOR,
                            role=self.role,
                            issue=f"Tempo {tempo} BPM is outside typical range [{lo}-{hi}] for '{genre}'.",
                        )
                    ]
                break
        return []


class InstrumentMismatchDetector(CritiqueRule):
    """Detect instruments unusual for the genre."""

    rule_id = "instrument_mismatch"
    role = Role.ARRANGEMENT

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check if instruments match genre expectations."""
        # Simplified: just check if electronic instruments in classical
        genre = plan.global_context.genre.lower()
        instruments = [name for name, _ in plan.global_context.instruments]

        if "classical" in genre or "baroque" in genre:
            electronic = [i for i in instruments if "synth" in i or "electric" in i]
            if electronic:
                return [
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=f"Electronic instruments {electronic} in classical genre.",
                    )
                ]
        return []
