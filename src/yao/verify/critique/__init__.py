"""Rule-based critique engine — Pillar 2 of v2.0 verification.

Provides structured, machine-actionable critique of MusicalPlans via
typed Finding objects. Each rule inherits CritiqueRule and emits
Finding objects — never free text.

Phase alpha: base types (CritiqueRule, Finding, registry).
Phase beta: 30+ rules across 6 roles.
"""

from __future__ import annotations
