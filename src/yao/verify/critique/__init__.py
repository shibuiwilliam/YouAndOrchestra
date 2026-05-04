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
from yao.verify.critique.metric_drift import MetricDriftDetector  # noqa: F401
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
# Surprise (2) — Phase γ.1
from yao.verify.critique.surprise_rules import (  # noqa: E402
    SurpriseDeficitDetector,
    SurpriseOverloadDetector,
)

CRITIQUE_RULES.register(SurpriseDeficitDetector())
CRITIQUE_RULES.register(SurpriseOverloadDetector())
# Tension (1) — Phase γ.1
from yao.verify.critique.tension_rules import (  # noqa: E402
    TensionArcUnresolvedDetector,
)

CRITIQUE_RULES.register(TensionArcUnresolvedDetector())
# Hook (3) — Phase γ.3
from yao.verify.critique.hook_rules import (  # noqa: E402
    HookMisplacementDetector,
    HookOveruseDetector,
    HookUnderuseDetector,
)

CRITIQUE_RULES.register(HookOveruseDetector())
CRITIQUE_RULES.register(HookUnderuseDetector())
CRITIQUE_RULES.register(HookMisplacementDetector())
# Dynamics (1) — Phase γ.3
from yao.verify.critique.dynamics_rules import (  # noqa: E402
    FlatPhraseDynamicsDetector,
)

CRITIQUE_RULES.register(FlatPhraseDynamicsDetector())
# Groove (3) — Phase γ.4
from yao.verify.critique.groove_rules import (  # noqa: E402
    EnsembleGrooveConflictDetector,
    GrooveInconsistencyDetector,
    MicrotimingFlatnessDetector,
)

CRITIQUE_RULES.register(GrooveInconsistencyDetector())
CRITIQUE_RULES.register(MicrotimingFlatnessDetector())
CRITIQUE_RULES.register(EnsembleGrooveConflictDetector())
# Conversation (4) — Phase γ.5
from yao.verify.critique.conversation_rules import (  # noqa: E402
    ConversationSilenceDetector,
    FillAbsenceDetector,
    FrequencyCollisionUnresolvedDetector,
    PrimaryVoiceAmbiguityDetector,
)

CRITIQUE_RULES.register(ConversationSilenceDetector())
CRITIQUE_RULES.register(PrimaryVoiceAmbiguityDetector())
CRITIQUE_RULES.register(FillAbsenceDetector())
CRITIQUE_RULES.register(FrequencyCollisionUnresolvedDetector())


# Metric rules (v2.0)
CRITIQUE_RULES.register(MetricDriftDetector())
