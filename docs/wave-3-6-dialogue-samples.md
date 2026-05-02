# Wave 3.6 — Sample Dialogue Transcripts

Three example `/sketch` multi-turn sessions.

---

## Sample 1: 雨の夜のカフェ (Japanese input)

**User:** `/sketch 雨の夜のカフェで流れるピアノ曲`

**Turn 1 (Emotion/Purpose):**
> Based on your description, I hear:
> - **Core emotion:** melancholic, introspective, peaceful
> - **Purpose:** cafe background music
> - **Listening context:** cafe speakers, evening ambiance
>
> Is this right?

**User:** yes, but more lonely than peaceful

**Turn 2 (References):**
> Drawing from:
> - *Impressionist piano* (Debussy-like harmonic ambiguity)
> - *Jazz ballad voicings* (extended chords, gentle movement)
> - *Ambient rain textures*
>
> Avoid: upbeat energy, electronic sounds, fast tempo
>
> Sound right?

**User:** yes

**Turn 3 (Structure):**
> - **Instruments:** piano (melody + harmony)
> - **Duration:** 90 seconds (loopable)
> - **Key:** D minor (melancholic, lonely)
> - **Tempo:** 68 BPM (slow, contemplative)
> - **Sections:** intro (4) → A (8) → B (8) → A' (8) → outro (4)
>
> Adjust anything?

**User:** make it 2 minutes, add cello

**Turn 4 (Trajectory):**
> ```
> Tension:  ░░▓▓▓▓▓▓████████▓▓▓▓░░░░
>           intro  A    B    A'  outro
> ```
> Peak in B section (lonely climax), then gentle descent.

**User:** yes

**Turn 5 (Confirm):** *Shows YAML* → **User:** looks good

**Turn 6:** Generates with `stochastic_v2`, seed=42, temp=0.4

---

## Sample 2: Game Boss Battle (English)

**User:** `/sketch epic boss battle music for an RPG, intense and dramatic`

**Turn 1:**
> - **Core emotion:** intense, threatening, epic
> - **Purpose:** RPG boss encounter BGM
> - **Listening context:** game speakers/headphones, high-focus combat
>
> Correct?

**User:** yes, should feel overwhelming but not hopeless

**Turn 2:**
> Drawing from: *orchestral film scores, Nobuo Uematsu style, brass + strings intensity*
> Avoid: peaceful melodies, slow pacing, ambient textures

**User:** add some choir feel too

**Turn 3:**
> - **Instruments:** strings_ensemble (melody), french_horn (counter), timpani (rhythm), organ (pad)
> - **Duration:** 120 seconds (loopable for combat)
> - **Key:** C minor (dark, dramatic)
> - **Tempo:** 155 BPM (driving, urgent)
> - **Sections:** intro (4) → battle_A (8) → battle_B (8) → breakdown (4) → climax (8) → loop_out (4)
>
> Loopable: yes (loop_out connects to battle_A)

**User:** perfect

**Turn 4:**
> Tension starts high (0.7), never drops below 0.5, peaks at 0.95 in climax.
> Density: constant high (0.8-1.0) except breakdown (0.4).

**User:** yes

**Turn 5/6:** Confirm → Generate at `stochastic_v2`, temp=0.7

---

## Sample 3: Simple Study Music (Minimal)

**User:** `/sketch something calm for studying`

**Turn 1:**
> - **Core emotion:** calm, focused, unobtrusive
> - **Purpose:** study/work background
> - **Listening context:** headphones, long sessions
>
> Right?

**User:** yes

**Turn 2:**
> Drawing from: *lo-fi hip-hop aesthetic, ambient piano, minimal repetition*
> Avoid: lyrics (obviously), dramatic changes, heavy bass

**User:** that works

**Turn 3:**
> - **Instruments:** piano (melody)
> - **Duration:** 90 seconds (loop)
> - **Key:** F major (warm, gentle)
> - **Tempo:** 75 BPM
> - **Sections:** intro (4) → loop_body (24) → outro (4)
> - **Loopable:** yes

**User:** yes but add some strings quietly

**Turn 4:**
> Tension: very flat (0.2-0.3), no peaks. Density: low (0.3-0.4).
> The point is to be **forgettable** (in a good way).

**User:** exactly

**Turn 5/6:** Confirm → Generate at `rule_based_v2`, temp=0.0 (deterministic, minimal)

---

## Key Design Decisions

1. **Concrete proposals, not open questions**: "D minor or F minor?" not "what key?"
2. **Each turn approvable with "yes"**: minimal friction for users who trust defaults
3. **State persists**: interrupt and `/sketch resume <name>` at any point
4. **SpecCompiler integration**: Turn 3 uses keyword→spec mapping from Wave 1.3
5. **V2 pipeline default**: `stochastic_v2` for creative pieces, `rule_based_v2` for deterministic
