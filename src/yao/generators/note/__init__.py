"""Note realizers — produce ScoreIR from MusicalPlan.

Only the plan-consuming v2 realizers remain. The deprecated legacy discard
realizers ("stochastic"/"rule_based") were retired once the default pipeline
routed to the v2 realizers (see ``note.base.resolve_realizer_name`` and
PROJECT_IMPROVEMENT.md §P1.1/§P4.4).
"""

from __future__ import annotations

# Import realizer modules to trigger @register_note_realizer decorators.
import yao.generators.note.rule_based_v2 as _rule_based_v2  # noqa: F401
import yao.generators.note.stochastic_v2 as _stochastic_v2  # noqa: F401
