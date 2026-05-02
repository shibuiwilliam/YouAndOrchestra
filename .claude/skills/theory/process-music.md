---
topic: process_music
applies_to: [generation]
---

# Process Music — Theory Skill

## Overview
Process music (minimalism) uses repetition and gradual transformation
of short melodic cells. Pioneered by Steve Reich and Philip Glass.

## Three Core Processes
1. **Phasing**: Two identical patterns gradually shift apart in time
2. **Additive**: Pattern grows by adding notes one at a time
3. **Subtractive**: Pattern shrinks by removing notes one at a time

## Key Characteristics
- Short cells (2-8 notes typically)
- Diatonic or modal (usually not chromatic)
- Steady pulse throughout
- Change is gradual and perceptible
- Texture emerges from overlapping patterns

## Phasing
- Two voices start in unison
- One voice shifts by a tiny amount each cycle
- Creates complex rhythmic interference patterns
- Hallmark of early Reich works

## Additive Process
- Start with 1 note of the cell
- Add one note per cycle until full cell is playing
- Then may start subtracting or cycling new cells
- Creates sense of organic growth

## Subtractive Process
- Start with full cell
- Remove one note per cycle
- Remaining notes become sparser
- Creates dissolution effect

## YaO Implementation
- `strategy: process_music` in composition.yaml
- Temperature controls process type:
  - Low (<0.35): phasing (most systematic)
  - Medium (0.35-0.65): additive
  - High (>0.65): subtractive
- Cell auto-generated from key/scale
