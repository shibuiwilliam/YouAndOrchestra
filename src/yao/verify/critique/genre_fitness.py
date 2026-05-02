"""Genre fitness critique rules — detect genre convention violations.

Rules:
- TempoOutOfRangeDetector: tempo outside typical genre range (Skill-driven)
- InstrumentMismatchDetector: instruments not typical for genre (Skill-driven)

v3.0 Wave 2.1: Sources tempo ranges and instrument lists from SkillRegistry
instead of hardcoded dicts. Falls back to hardcoded if Skill not found.

Belongs to Layer 6 (Verification).
"""

from __future__ import annotations

from yao.ir.plan.musical_plan import MusicalPlan
from yao.schema.composition_v2 import CompositionSpecV2
from yao.skills.loader import get_skill_registry
from yao.verify.critique.base import CritiqueRule
from yao.verify.critique.types import Finding, Role, Severity

# Fallback tempo ranges when no Skill is available
_FALLBACK_GENRE_TEMPO: dict[str, tuple[float, float]] = {
    "cinematic": (60, 160),
    "jazz": (80, 220),
    "rock": (100, 150),
    "pop": (90, 140),
    "edm": (120, 140),
    "classical": (40, 160),
    "ambient": (60, 100),
}


class TempoOutOfRangeDetector(CritiqueRule):
    """Detect tempo outside typical genre range.

    v3.0: First checks SkillRegistry for genre-specific tempo range.
    Falls back to hardcoded dict if genre not found in registry.
    """

    rule_id = "tempo_out_of_range"
    role = Role.ARRANGEMENT

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check tempo against genre conventions from SkillRegistry."""
        genre = plan.global_context.genre.lower()
        tempo = plan.global_context.tempo_bpm

        # Try SkillRegistry first
        registry = get_skill_registry()
        tempo_range = registry.tempo_range_for(genre)

        if tempo_range is not None:
            lo, hi = tempo_range
            source = "skill"
        else:
            # Fallback to hardcoded dict
            for genre_key, (flo, fhi) in _FALLBACK_GENRE_TEMPO.items():
                if genre_key in genre:
                    lo, hi = flo, fhi
                    source = "fallback"
                    break
            else:
                return []

        if tempo < lo or tempo > hi:
            return [
                Finding(
                    rule_id=self.rule_id,
                    severity=Severity.MINOR,
                    role=self.role,
                    issue=f"Tempo {tempo} BPM is outside typical range [{lo}-{hi}] for '{genre}'.",
                    evidence={
                        "tempo": tempo,
                        "range": [lo, hi],
                        "genre": genre,
                        "source": source,
                    },
                )
            ]
        return []


class InstrumentMismatchDetector(CritiqueRule):
    """Detect instruments unusual for the genre.

    v3.0: Checks against SkillRegistry's avoided_instruments list.
    Falls back to basic electronic-in-classical check.
    """

    rule_id = "instrument_mismatch"
    role = Role.ARRANGEMENT

    def detect(self, plan: MusicalPlan, spec: CompositionSpecV2) -> list[Finding]:
        """Check if instruments match genre expectations from SkillRegistry."""
        genre = plan.global_context.genre.lower()
        instruments = [name for name, _ in plan.global_context.instruments]

        # Try SkillRegistry first
        registry = get_skill_registry()
        profile = registry.get_genre(genre)

        if profile is not None and profile.avoided_instruments:
            mismatched = [i for i in instruments if i in profile.avoided_instruments]
            if mismatched:
                return [
                    Finding(
                        rule_id=self.rule_id,
                        severity=Severity.MINOR,
                        role=self.role,
                        issue=(f"Instruments {mismatched} are in the avoided list for genre '{genre}'."),
                        evidence={
                            "mismatched": mismatched,
                            "genre": genre,
                            "avoided": list(profile.avoided_instruments),
                            "source": "skill",
                        },
                    )
                ]
            return []

        # Fallback: basic electronic-in-classical check
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
