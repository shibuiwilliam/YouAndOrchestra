# /sketch — 6-turn interactive sketch-to-spec dialogue

Transform a musical idea into a complete specification through a structured 6-turn dialogue.
Each turn proposes concrete suggestions; the user approves or adjusts.

**Input:** `$ARGUMENTS` — Optional initial description. If empty, start Turn 1 with an open question.

## State Management

Store dialogue state in `specs/projects/<name>/sketch_state.json`:
```json
{
  "turn": 2,
  "project_name": "rainy-cafe",
  "intent": { "emotion": "melancholic", "purpose": "study bgm", "context": "rainy night" },
  "references": { "like": ["Debussy preludes"], "avoid": ["harsh electronic"] },
  "instruments": ["piano"],
  "duration_seconds": 90,
  "trajectory_shape": "arc",
  "spec_draft": { ... }
}
```

To resume: `/sketch resume <name>` loads the state and continues from the saved turn.

---

## Turn 1: Core Emotion & Purpose

**Goal:** Establish the emotional core and listening context.

If `$ARGUMENTS` is provided, extract emotion/purpose from it and present:

"Based on your description, I hear:
- **Core emotion:** melancholic, introspective
- **Purpose:** background music for studying/reading
- **Listening context:** alone, headphones, evening

Is this right? Anything to adjust?"

If `$ARGUMENTS` is empty, ask:
"Let's build your piece together. Tell me:
1. What **feeling** should this music evoke? (e.g., peaceful, tense, triumphant, nostalgic)
2. What is it **for**? (e.g., game menu, study BGM, film scene, personal enjoyment)
3. Where will it be **heard**? (e.g., headphones alone, cafe speakers, live performance)"

**Save:** emotion, purpose, context → `sketch_state.json`

---

## Turn 2: References & Anti-References

"Now let's define the sound world:

**Draw inspiration from** (style, not specific copyrighted melodies):
- I'd suggest: *Debussy-like impressionism, soft jazz voicings, sparse piano*
  (based on your 'melancholic evening' intent)

**Avoid:**
- Harsh timbres, fast tempos, major-key brightness?

Are these right? Name any artists/genres/moods to draw from or avoid."

**Save:** like_references, avoid_references → `sketch_state.json`

---

## Turn 3: Instruments, Duration, Structure

"Here's what I'd suggest for your piece:

- **Instruments:** piano (melody), cello (bass line), strings pad
- **Duration:** ~90 seconds (good for a study loop)
- **Sections:** intro (4 bars) → A (8 bars) → B (8 bars) → A' (8 bars) → outro (4 bars)
- **Key:** D minor (melancholic)
- **Tempo:** 72 BPM (slow, contemplative)
- **Loopable:** yes (outro connects back to intro)

Adjust any of these? I can change instruments, add/remove sections, or shift the feel."

**Derive:** Use `src/yao/sketch/compiler.py` keyword matching + emotion vocabulary to propose concrete values.

**Save:** instruments, duration, sections, key, tempo → `sketch_state.json`

---

## Turn 4: Trajectory (Emotional Arc)

"Here's the emotional arc I'd suggest:

```
Tension:  ░░▓▓▓▓▓▓████████▓▓▓▓░░
Density:  ░░▓▓▓▓▓▓████████▓▓▓▓░░
          intro  A    B    A'  outro
```

- **Tension:** starts 0.2, rises to 0.5 in A, peaks at 0.7 in B, returns to 0.3 in A', ends 0.15
- **Density:** mirrors tension — sparse intro, moderate verse, fullest in B
- **Climax:** section B (the emotional peak)

Does this arc feel right? I can make it more dramatic, more flat, or shift the peak."

**Save:** trajectory waypoints, climax section → `sketch_state.json`

---

## Turn 5: Final Spec Confirmation

Present the complete spec as YAML preview:

"Here's your complete specification:

```yaml
title: Rainy Night Café
key: D minor
tempo_bpm: 72
time_signature: 4/4
instruments:
  - name: piano, role: melody
  - name: cello, role: bass
sections:
  - name: intro, bars: 4, dynamics: pp
  - name: verse_a, bars: 8, dynamics: mp
  - name: bridge, bars: 8, dynamics: mf
  - name: verse_b, bars: 8, dynamics: mp
  - name: outro, bars: 4, dynamics: pp
generation:
  strategy: stochastic_v2
  seed: 42
  temperature: 0.4
```

**intent.md:**
> A melancholic piano piece for studying on a rainy evening. Inspired by impressionist harmony, with gentle cello support. Quiet, introspective, loopable.

Ready to create? I'll write the files and validate."

**On approval:** Write `composition.yaml`, `trajectory.yaml`, `intent.md`. Run `yao validate`.

---

## Turn 6: Generate & Review

"Your project is ready! Generating now..."

```bash
yao conduct --spec specs/projects/<name>/composition.yaml --project <name> --iterations 3
```

After generation:
1. Show evaluation summary + aesthetic scores
2. If issues: offer `/critique <name>` or `/regenerate-section`
3. If good: offer `/render <name>` for audio

---

## Resume Protocol

`/sketch resume <name>`:
1. Load `specs/projects/<name>/sketch_state.json`
2. Report: "Resuming sketch for '<name>' — we were on Turn {N}."
3. Continue from the saved turn

---

## Rules
- **Offer concrete suggestions, not open-ended questions** ("D minor or F minor?" not "what key?")
- **Each turn must be approvable with a single "yes"** — but adjustable with specifics
- **Explain musical choices briefly** ("D minor because you said melancholic")
- **Save state after each turn** (enables resume)
- **Use Wave 1.3 SpecCompiler** for keyword → spec translation
- **Use Wave 3.4 StyleVector** vocabulary when describing reference styles
- **Never generate without user approval of the complete spec** (Turn 5)
- **Generator default: stochastic_v2** (V2 pipeline, direct plan consumption)
