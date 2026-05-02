"""Rule-based critique engine — 15+ machine-detected rules (P4).

Provides structured, machine-actionable critique of MusicalPlans via
typed Finding objects. Each rule inherits CritiqueRule and emits
Finding objects — never free text.

15 rules across 6 roles: structural (3), harmonic (3), melodic (3),
rhythmic (2), arrangement (2), emotional (2).
"""

from __future__ import annotations

from yao.verify.critique.arrangement import (  # noqa: F401
    FrequencyCollisionDetector,
    TextureCollapseDetector,
)
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
from yao.verify.critique.rhythmic import (  # noqa: F401
    RhythmicMonotonyDetector,
    SyncopationLackDetector,
)
from yao.verify.critique.structural import (  # noqa: F401
    ClimaxAbsenceDetector,
    FormImbalanceDetector,
    SectionMonotonyDetector,
)

# Register all 15 rules
# Structural (3)
CRITIQUE_RULES.register(SectionMonotonyDetector())
CRITIQUE_RULES.register(ClimaxAbsenceDetector())
CRITIQUE_RULES.register(FormImbalanceDetector())
# Harmonic (3)
CRITIQUE_RULES.register(ClicheChordProgressionDetector())
CRITIQUE_RULES.register(CadenceWeaknessDetector())
CRITIQUE_RULES.register(HarmonicMonotonyDetector())
# Melodic (3)
CRITIQUE_RULES.register(ContourMonotonyDetector())
CRITIQUE_RULES.register(MotifRecurrenceDetector())
CRITIQUE_RULES.register(PhraseClosureWeaknessDetector())
# Rhythmic (2)
CRITIQUE_RULES.register(RhythmicMonotonyDetector())
CRITIQUE_RULES.register(SyncopationLackDetector())
# Arrangement (2)
CRITIQUE_RULES.register(FrequencyCollisionDetector())
CRITIQUE_RULES.register(TextureCollapseDetector())
# Emotional (2)
CRITIQUE_RULES.register(IntentDivergenceDetector())
CRITIQUE_RULES.register(TrajectoryViolationDetector())
# Memorability (2) — NEW
from yao.verify.critique.memorability import (  # noqa: E402
    HookWeaknessDetector,
    MotifAbsenceDetector,
)

CRITIQUE_RULES.register(MotifAbsenceDetector())
CRITIQUE_RULES.register(HookWeaknessDetector())
# Genre Fitness (2) — NEW
from yao.verify.critique.genre_fitness import (  # noqa: E402
    InstrumentMismatchDetector,
    TempoOutOfRangeDetector,
)

CRITIQUE_RULES.register(TempoOutOfRangeDetector())
CRITIQUE_RULES.register(InstrumentMismatchDetector())
