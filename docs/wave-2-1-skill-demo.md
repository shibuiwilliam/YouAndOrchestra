# Wave 2.1 Skill Grounding Demo

> **Date**: 2026-05-03
> **Gap**: Gap-3 (Genre Skills not integrated into generation pipeline)
> **Status**: RESOLVED

## Scenario

- Genre: `jazz_swing`
- Key: D minor, 140 BPM, 8 bars
- Same spec used in both cases (only the skill YAML differs)

## Before: Original jazz_swing.yaml

```yaml
typical_chord_progressions:
  - [ii7, V7, Imaj7]
  - [Imaj7, vi7, ii7, V7]
  - [I7, IV7, I7, V7]
  - [iii7, vi7, ii7, V7]
```

**Skill source**: jazz_swing (from SkillRegistry)
**First 8 chord events**: `ii7, V7, Imaj7, vi7, I7, IV7, iii7, ii7`

## After: Modified jazz_swing.yaml

```yaml
typical_chord_progressions:
  - [i, bVII, bVI, V]
  - [i, bVII, bVI, V7]
```

**Skill source**: jazz_swing (same)
**First 8 chord events**: `i, bVII, bVI, V, V7, i, bVII, bVI`

## Verification

| Position | Before | After | Changed? |
|----------|--------|-------|----------|
| 1 | ii7 | i | Yes |
| 2 | V7 | bVII | Yes |
| 3 | Imaj7 | bVI | Yes |
| 4 | vi7 | V | Yes |
| 5 | I7 | V7 | Yes |
| 6 | IV7 | i | Yes |
| 7 | iii7 | bVII | Yes |
| 8 | ii7 | bVI | Yes |

**All 8/8 chord positions changed** when the skill file was edited.

## Provenance

Both generations recorded `source_skill: "jazz_swing"` in the harmony_planning provenance entry, confirming the Skill was the source of the chord palette.

## Conclusion

Editing `.claude/skills/genres/jazz_swing.md` (which syncs to `src/yao/skills/genres/jazz_swing.yaml`) directly changes the chord progression output of the HarmonyPlanner. This proves:

1. **SkillRegistry** loads genre profiles from YAML
2. **HarmonyPlanner** reads chord_palette from the registry
3. **Skill edits propagate to generation output**
4. **Provenance tracks the source** (`source_skill` field)

The YaO promise that "musicians can edit Markdown to change generation behavior" is now a reality for chord progressions.

### Integration Points Demonstrated

| Point | Module | Skill Field Used | Status |
|-------|--------|------------------|--------|
| HarmonyPlanner | `harmony_planner.py` | `typical_chord_progressions` | ✅ |
| SpecCompiler | `compiler.py` | `preferred_instruments`, `typical_keys`, `tempo_range` | ✅ |
| Genre Fitness Critique | `genre_fitness.py` | `tempo_range`, `avoided_instruments` | ✅ |
| DrumPatterner | `drum_patterner.py` | `typical_drum_pattern` | Planned |
| Performance Pipeline | `pipeline.py` | `default_swing` | Planned |
