"""Feedback — Pin processing and NL feedback translation.

Provides three-tier feedback granularity:
  1. Spec-level: change YAML, regenerate everything (existing)
  2. Section-level: regenerate-section (existing)
  3. Pin-level: attach localized comment, targeted regeneration (NEW)

Belongs to Layer 1.5 (between user input and generation).
"""

from __future__ import annotations
