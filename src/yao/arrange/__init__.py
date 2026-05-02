"""Arrangement Engine — transform existing music under preservation contracts.

MVP implementation:
- SourcePlanExtractor: MIDI → MusicalPlan (simplified MIR)
- StyleVectorOps: style transfer via vector arithmetic
- ArrangementDiffWriter: markdown diff output
- Arrangement critique rules (4 rules)
"""

from __future__ import annotations
