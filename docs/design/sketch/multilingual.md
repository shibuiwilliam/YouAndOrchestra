# Design: Multilingual SpecCompiler

## Problem

YaO only supports English input. Japanese users cannot describe their musical intent naturally.

## Solution

Extend SpecCompiler with Japanese keyword + emotion vocabulary support. Language auto-detected via CJK character ratio heuristic.

## Architecture

- `language_detect.py`: ASCII ratio heuristic (< 50% ASCII → Japanese)
- `emotion_vocabulary.py`: 50+ Japanese emotion words mapped to valence × arousal → key/tempo/instruments
- `compiler.py`: Japanese-specific parsing for instruments (ピアノ, チェロ...), tempo (ゆっくり, 速い...), duration (90秒, 2分), genre

## Extended Scales

28 scales total:
- 14 standard Western (major, minor, modes, pentatonic, blues, etc.)
- 6 Japanese (in, yo, ritsu, minyo, hirajoshi, iwato)
- 5 Maqam (hijaz, kurd, nahawand, bayati, rast)
- 5 Raga (marwa, todi, bhairav, yaman, puriya)
- 2 Gamelan (pelog, slendro)
- 1 Just intonation

## Custom Instruments

8 non-Western profiles: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney. Each includes cultural_origin, idiomatic_techniques, GM approximation with custom_sf2_path option.

## Culture Skills

3 skills with academic source citations:
- Japanese (jo-ha-kyū form, pentatonic traditions)
- Middle Eastern (maqam system, quarter-tone intervals)
- Indian Classical (raga system, tala rhythmic cycles)

## Files

- `src/yao/sketch/language_detect.py` — auto-detection
- `src/yao/sketch/emotion_vocabulary.py` — 50+ Japanese emotion words
- `src/yao/sketch/compiler.py` — SpecCompiler with 3-stage fallback
- `src/yao/constants/scales.py` — 28 scale definitions
- `src/yao/constants/custom_instruments.py` — 8 cultural instruments
- `.claude/skills/cultures/` — 3 culture skill files
