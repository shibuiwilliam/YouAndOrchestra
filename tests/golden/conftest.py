"""Golden test fixtures."""

from __future__ import annotations

# Ensure generators are registered for golden tests
import yao.generators.note.rule_based as _nrb  # noqa: F401
import yao.generators.note.stochastic as _nst  # noqa: F401
import yao.generators.rule_based as _rb  # noqa: F401
import yao.generators.stochastic as _st  # noqa: F401
