---
skill_id: emotion_mapping
display_name: "Emotion-to-Music Mapping"
description: "Maps emotional words (Japanese and English) to musical parameters via valence-arousal dimensions"
source: "Based on Russell's circumplex model of affect and Juslin & Sloboda (2001) Handbook of Music and Emotion"
---

# Emotion-to-Music Mapping

This skill provides a structured mapping from emotional descriptors to musical parameters.
Each emotion is placed on a **valence** (positive/negative) x **arousal** (high/low energy) plane,
with corresponding suggestions for key, mode, tempo range, and instrumentation hints.

## Valence-Arousal Model

```
         High Arousal
              |
   angry     |     excited
   tense     |     energetic
              |
 -Valence ---+--- +Valence
              |
   sad       |     calm
   melancholy|     peaceful
              |
         Low Arousal
```

## Vocabulary

```yaml
emotions:
  ja:
    # ── Positive valence, high arousal ──
    嬉しい: { valence: 0.7, arousal: 0.6, key: "D major", mode: "major", tempo: "fast", instruments: [] }
    楽しい: { valence: 0.8, arousal: 0.7, key: "G major", mode: "major", tempo: "fast", instruments: [] }
    爽やか: { valence: 0.5, arousal: 0.4, key: "A major", mode: "major", tempo: "moderate", instruments: [] }
    明るい: { valence: 0.6, arousal: 0.5, key: "C major", mode: "major", tempo: "moderate", instruments: [] }
    元気: { valence: 0.7, arousal: 0.8, key: "A major", mode: "major", tempo: "fast", instruments: [] }
    勇壮: { valence: 0.7, arousal: 0.8, key: "Bb major", mode: "major", tempo: "fast", instruments: ["french_horn", "strings_ensemble"] }
    壮大: { valence: 0.5, arousal: 0.7, key: "D minor", mode: "minor", tempo: "moderate", instruments: ["strings_ensemble", "french_horn"] }
    力強い: { valence: 0.4, arousal: 0.8, key: "C minor", mode: "minor", tempo: "fast", instruments: ["piano", "strings_ensemble"] }
    華やか: { valence: 0.6, arousal: 0.6, key: "F major", mode: "major", tempo: "moderate", instruments: ["piano", "violin"] }
    躍動的: { valence: 0.5, arousal: 0.9, key: "E major", mode: "major", tempo: "very_fast", instruments: [] }

    # ── Positive valence, low arousal ──
    穏やか: { valence: 0.4, arousal: -0.3, key: "F major", mode: "major", tempo: "slow", instruments: ["piano"] }
    安らぎ: { valence: 0.5, arousal: -0.5, key: "G major", mode: "major", tempo: "slow", instruments: ["piano", "acoustic_guitar_nylon"] }
    優しい: { valence: 0.4, arousal: -0.2, key: "F major", mode: "major", tempo: "slow", instruments: ["piano"] }
    温かい: { valence: 0.5, arousal: -0.1, key: "E major", mode: "major", tempo: "moderate", instruments: ["piano", "cello"] }
    瑞々しい: { valence: 0.4, arousal: 0.3, key: "G major", mode: "major", tempo: "moderate", instruments: [] }
    清らか: { valence: 0.3, arousal: -0.2, key: "C major", mode: "major", tempo: "slow", instruments: ["piano"] }
    のどか: { valence: 0.4, arousal: -0.4, key: "F major", mode: "major", tempo: "slow", instruments: ["acoustic_guitar_nylon"] }
    幸福: { valence: 0.8, arousal: 0.1, key: "C major", mode: "major", tempo: "moderate", instruments: [] }
    希望: { valence: 0.6, arousal: 0.3, key: "D major", mode: "major", tempo: "moderate", instruments: [] }
    癒し: { valence: 0.3, arousal: -0.6, key: "F major", mode: "major", tempo: "slow", instruments: ["piano", "acoustic_guitar_nylon"] }

    # ── Negative valence, low arousal ──
    悲しい: { valence: -0.6, arousal: -0.3, key: "D minor", mode: "minor", tempo: "slow", instruments: ["piano", "cello"] }
    切ない: { valence: -0.4, arousal: 0.0, key: "A minor", mode: "minor", tempo: "moderate", instruments: ["piano"] }
    寂しい: { valence: -0.5, arousal: -0.4, key: "E minor", mode: "minor", tempo: "slow", instruments: ["piano"] }
    儚い: { valence: -0.2, arousal: -0.4, key: "F# minor", mode: "minor", tempo: "slow", instruments: ["piano", "violin"] }
    憂鬱: { valence: -0.6, arousal: -0.5, key: "C minor", mode: "minor", tempo: "slow", instruments: ["piano"] }
    物悲しい: { valence: -0.5, arousal: -0.3, key: "D minor", mode: "minor", tempo: "slow", instruments: ["cello", "piano"] }
    哀愁: { valence: -0.4, arousal: -0.1, key: "A minor", mode: "minor", tempo: "moderate", instruments: ["violin", "piano"] }
    ノスタルジー: { valence: -0.2, arousal: -0.2, key: "A minor", mode: "minor", tempo: "moderate", instruments: ["piano"] }
    郷愁: { valence: -0.2, arousal: -0.3, key: "G minor", mode: "minor", tempo: "slow", instruments: ["acoustic_guitar_nylon"] }
    感傷的: { valence: -0.3, arousal: -0.1, key: "E minor", mode: "minor", tempo: "moderate", instruments: ["piano", "strings_ensemble"] }

    # ── Negative valence, high arousal ──
    怒り: { valence: -0.7, arousal: 0.8, key: "C minor", mode: "minor", tempo: "fast", instruments: ["piano"] }
    緊張: { valence: -0.3, arousal: 0.6, key: "B minor", mode: "minor", tempo: "moderate", instruments: ["strings_ensemble"] }
    不安: { valence: -0.4, arousal: 0.4, key: "E minor", mode: "minor", tempo: "moderate", instruments: ["strings_ensemble", "piano"] }
    恐怖: { valence: -0.6, arousal: 0.7, key: "C minor", mode: "minor", tempo: "moderate", instruments: ["strings_ensemble"] }
    激しい: { valence: -0.2, arousal: 0.9, key: "D minor", mode: "minor", tempo: "very_fast", instruments: ["piano"] }
    焦燥: { valence: -0.5, arousal: 0.7, key: "F minor", mode: "minor", tempo: "fast", instruments: ["piano", "strings_ensemble"] }
    荒々しい: { valence: -0.3, arousal: 0.9, key: "C minor", mode: "minor", tempo: "very_fast", instruments: [] }

    # ── Neutral / mixed ──
    神秘的: { valence: 0.0, arousal: 0.1, key: "A minor", mode: "minor", tempo: "slow", instruments: ["synth_pad_warm", "piano"] }
    幻想的: { valence: 0.1, arousal: 0.0, key: "F# minor", mode: "minor", tempo: "slow", instruments: ["synth_pad_warm", "piano"] }
    ドラマチック: { valence: 0.0, arousal: 0.7, key: "C minor", mode: "minor", tempo: "moderate", instruments: ["strings_ensemble", "piano"] }
    壮厳: { valence: 0.1, arousal: 0.3, key: "D minor", mode: "minor", tempo: "slow", instruments: ["strings_ensemble", "french_horn"] }
    厳か: { valence: 0.0, arousal: -0.2, key: "D minor", mode: "minor", tempo: "slow", instruments: ["strings_ensemble"] }
    静寂: { valence: 0.0, arousal: -0.7, key: "E minor", mode: "minor", tempo: "slow", instruments: ["piano"] }
    夢幻: { valence: 0.1, arousal: -0.3, key: "F major", mode: "major", tempo: "slow", instruments: ["synth_pad_warm", "piano"] }
    懐かしい: { valence: 0.1, arousal: -0.2, key: "G major", mode: "major", tempo: "moderate", instruments: ["piano", "acoustic_guitar_nylon"] }
    甘美: { valence: 0.3, arousal: -0.1, key: "Ab major", mode: "major", tempo: "slow", instruments: ["violin", "piano"] }
    可憐: { valence: 0.2, arousal: -0.1, key: "F major", mode: "major", tempo: "moderate", instruments: ["piano", "violin"] }
    雄大: { valence: 0.3, arousal: 0.5, key: "D major", mode: "major", tempo: "moderate", instruments: ["strings_ensemble", "french_horn"] }
    情熱的: { valence: 0.2, arousal: 0.8, key: "E minor", mode: "minor", tempo: "fast", instruments: ["piano", "violin"] }
    官能的: { valence: 0.1, arousal: 0.3, key: "Eb major", mode: "major", tempo: "slow", instruments: ["saxophone_alto", "piano"] }

  en:
    happy: { valence: 0.7, arousal: 0.5, key: "C major", mode: "major", tempo: "moderate" }
    joyful: { valence: 0.8, arousal: 0.6, key: "D major", mode: "major", tempo: "fast" }
    bright: { valence: 0.5, arousal: 0.4, key: "G major", mode: "major", tempo: "moderate" }
    triumphant: { valence: 0.7, arousal: 0.7, key: "D major", mode: "major", tempo: "fast" }
    energetic: { valence: 0.5, arousal: 0.8, key: "A major", mode: "major", tempo: "fast" }
    calm: { valence: 0.3, arousal: -0.4, key: "F major", mode: "major", tempo: "slow" }
    peaceful: { valence: 0.4, arousal: -0.5, key: "F major", mode: "major", tempo: "slow" }
    gentle: { valence: 0.3, arousal: -0.3, key: "G major", mode: "major", tempo: "slow" }
    sad: { valence: -0.6, arousal: -0.3, key: "D minor", mode: "minor", tempo: "slow" }
    melancholic: { valence: -0.5, arousal: -0.2, key: "D minor", mode: "minor", tempo: "slow" }
    dark: { valence: -0.5, arousal: 0.2, key: "C minor", mode: "minor", tempo: "moderate" }
    mysterious: { valence: 0.0, arousal: 0.1, key: "A minor", mode: "minor", tempo: "slow" }
    suspenseful: { valence: -0.3, arousal: 0.5, key: "E minor", mode: "minor", tempo: "moderate" }
    dramatic: { valence: 0.0, arousal: 0.7, key: "C minor", mode: "minor", tempo: "moderate" }
    epic: { valence: 0.3, arousal: 0.8, key: "D minor", mode: "minor", tempo: "moderate" }
    romantic: { valence: 0.4, arousal: 0.0, key: "E major", mode: "major", tempo: "slow" }
    nostalgic: { valence: -0.1, arousal: -0.2, key: "A minor", mode: "minor", tempo: "moderate" }
    dreamy: { valence: 0.2, arousal: -0.4, key: "F major", mode: "major", tempo: "slow" }
    contemplative: { valence: 0.0, arousal: -0.3, key: "E minor", mode: "minor", tempo: "slow" }
    tense: { valence: -0.4, arousal: 0.6, key: "B minor", mode: "minor", tempo: "moderate" }
    heroic: { valence: 0.6, arousal: 0.8, key: "Bb major", mode: "major", tempo: "fast" }
    introspective: { valence: 0.0, arousal: -0.4, key: "F# minor", mode: "minor", tempo: "slow" }
```

## Tempo Mapping

| Hint | BPM Range |
|------|-----------|
| very_slow | 50-65 |
| slow | 65-85 |
| moderate | 85-115 |
| fast | 115-150 |
| very_fast | 150-180 |

## Valence-Arousal → Musical Parameters

When multiple emotion words are detected, average their valence and arousal values,
then use the following mappings:

| Parameter | Low V / Low A | Low V / High A | High V / Low A | High V / High A |
|-----------|---------------|----------------|----------------|-----------------|
| Mode | minor | minor | major | major |
| Tempo | slow | fast | slow | fast |
| Dynamics | pp-mp | mf-ff | pp-mp | mf-ff |
| Register | low-mid | full | mid-high | full |

## References

- Russell, J.A. (1980). A circumplex model of affect. Journal of Personality and Social Psychology, 39(6), 1161-1178.
- Juslin, P.N. & Sloboda, J.A. (2001). Music and Emotion: Theory and Research. Oxford University Press.
- Eerola, T. & Vuoskoski, J.K. (2011). A comparison of the discrete and dimensional models of emotion in music. Psychology of Music, 39(1), 18-49.
