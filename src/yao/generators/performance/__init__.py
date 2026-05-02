"""Performance Realizers — Step 6.5 of the pipeline.

Four independent realizers that overlay performance expression on ScoreIR:
1. ArticulationRealizer — legato/staccato/accent
2. DynamicsCurveRenderer — smooth dynamics curves
3. MicrotimingInjector — genre-specific timing offsets
4. CCCurveGenerator — CC automation (vibrato, breath, pedal)
"""

from __future__ import annotations
