"""Rule-based critique engine — Pillar 2 of v2.0 verification.

Provides structured, machine-actionable critique of MusicalPlans via
typed Finding objects. Each rule inherits CritiqueRule and emits
Finding objects — never free text.

Phase α: base types (CritiqueRule, Finding, registry) + 12 initial rules.
Phase β target: 30+ rules across 6 roles.
"""

from __future__ import annotations

from yao.verify.critique.emotional import (  # noqa: F401
    IntentDivergenceDetector,
    TrajectoryViolationDetector,
)
from yao.verify.critique.harmonic import (  # noqa: F401
    CadenceWeaknessDetector,
    ClicheChordProgressionDetector,
    HarmonicMonotonyDetector,
)
from yao.verify.critique.melodic import (  # noqa: F401
    ContourMonotonyDetector,
    MotifRecurrenceDetector,
    PhraseClosureWeaknessDetector,
)
from yao.verify.critique.registry import CRITIQUE_RULES as CRITIQUE_RULES
from yao.verify.critique.rhythmic import RhythmicMonotonyDetector  # noqa: F401
from yao.verify.critique.structural import (  # noqa: F401
    ClimaxAbsenceDetector,
    FormImbalanceDetector,
    SectionMonotonyDetector,
)

# Register all rules
CRITIQUE_RULES.register(SectionMonotonyDetector())
CRITIQUE_RULES.register(ClimaxAbsenceDetector())
CRITIQUE_RULES.register(FormImbalanceDetector())
CRITIQUE_RULES.register(ClicheChordProgressionDetector())
CRITIQUE_RULES.register(CadenceWeaknessDetector())
CRITIQUE_RULES.register(HarmonicMonotonyDetector())
CRITIQUE_RULES.register(ContourMonotonyDetector())
CRITIQUE_RULES.register(MotifRecurrenceDetector())
CRITIQUE_RULES.register(PhraseClosureWeaknessDetector())
CRITIQUE_RULES.register(RhythmicMonotonyDetector())
CRITIQUE_RULES.register(IntentDivergenceDetector())
CRITIQUE_RULES.register(TrajectoryViolationDetector())
