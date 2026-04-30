"""Note realizers — produce ScoreIR from MusicalPlan."""

from __future__ import annotations

# Import realizer modules to trigger @register_note_realizer decorators.
import yao.generators.note.rule_based as _rule_based  # noqa: F401
import yao.generators.note.stochastic as _stochastic  # noqa: F401
