# Design: Arrangement Engine

## Problem

Many AI tools generate fresh music but cannot transform existing pieces under explicit contracts. Users need to rearrange, restyle, and adapt existing compositions while preserving specified elements.

## Solution

- **SourcePlanExtractor**: MIDI → MusicalPlan with confidence scores per extracted element
- **StyleVectorOps**: abstract feature vectors (tempo, density, spectral, groove, energy) for copyright-safe style transfer
- **PreservationContract**: minimum similarity thresholds enforced as hard errors — if melody preservation drops below threshold, the arrangement is rejected
- **DiffWriter**: Markdown arrangement diff (preserved/changed/risks)
- **ArrangementSpec**: schema with required `rights_status` field — no arrangement without explicit rights declaration

## Critique Rules

4 arrangement-specific critique rules evaluate the quality of transformations:
- FrequencyCollisionDetector
- TextureCollapseDetector
- EnsembleRegisterViolationDetector
- (plus general arrangement rules from the main critique registry)

## Files

- `src/yao/arrange/extractor.py` — SourcePlanExtractor
- `src/yao/arrange/style_vector_ops.py` — StyleVectorOps, PreservationContract
- `src/yao/arrange/diff_writer.py` — ArrangementDiffWriter
- `src/yao/arrange/critique_rules.py` — arrangement critique rules
- `src/yao/schema/arrangement.py` — ArrangementSpec
