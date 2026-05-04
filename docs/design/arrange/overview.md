# Design: Arrangement Engine (Phase δ.1)

## Problem
Many AI tools generate fresh music but cannot transform existing pieces under explicit contracts.

## Solution
- SourcePlanExtractor: MIDI → MusicalPlan with confidence scores
- StyleVectorOps: abstract feature vectors (tempo, density, spectral, groove, energy)
- PreservationContract: minimum similarity thresholds enforced as hard errors
- DiffWriter: Markdown arrangement diff (preserved/changed/risks)
- 4 arrangement critique rules
- ArrangementSpec schema with required rights_status field
