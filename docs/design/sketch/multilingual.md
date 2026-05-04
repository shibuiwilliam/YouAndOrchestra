# Design: Multilingual SpecCompiler (Phase γ.7)

## Problem
YaO only supports English input. Japanese users cannot describe their musical intent naturally.

## Solution
Extend SpecCompiler with Japanese keyword + emotion vocabulary support. Language auto-detected via CJK character ratio heuristic.

## Architecture
- `language_detect.py`: ASCII ratio heuristic (< 50% ASCII → Japanese)
- `emotion_vocabulary.py`: 50+ Japanese emotion words mapped to valence × arousal → key/tempo/instruments
- `compiler.py`: Japanese-specific parsing for instruments (ピアノ, チェロ...), tempo (ゆっくり, 速い...), duration (90秒, 2分), genre

## Extended Scales
17 → 28 scales. Added: japanese_in, japanese_yo, japanese_ritsu, japanese_minyo, hirajoshi, iwato, maqam_hijaz, maqam_kurd, maqam_nahawand, raga_marwa, raga_todi.

## Custom Instruments
8 non-Western profiles: shakuhachi, koto, shamisen, taiko, sitar, tabla, oud, ney. GM approximations with documented limitations.

## Culture Skills
3 skills (japanese, middle_eastern, indian_classical) with academic source citations.
