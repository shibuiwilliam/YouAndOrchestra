# Using YaO with Claude Code

YaO is designed to be used interactively through Claude Code. Here are the three ways to create music, from simplest to most control.

---

## Method 1: Just Ask (natural language)

Open Claude Code in the YaO directory and describe what you want:

> "Create a calm 90-second piano piece in D minor for studying. Build slowly to a gentle peak, then fade out."

Claude Code will:
1. Create a project with `yao new-project`
2. Write a composition spec matching your description
3. Run `yao conduct` to generate MIDI with automatic feedback-driven iteration
4. Show you the analysis and evaluation
5. Tell you where the files are

---

## Method 2: Slash Commands (guided workflow)

### `/sketch` — Design your music interactively

```
/sketch a melancholic piece for a rainy afternoon
```

Claude Code will guide you through choices:
- Key and tempo suggestions with musical reasoning
- Instrument selection from 54 available instruments (including 8 non-Western cultural)
- Section structure (intro/verse/chorus/outro)
- Dynamic arc and trajectory curves
- Writes the YAML spec and validates it for you

### `/compose` — Generate with the Conductor

```
/compose rainy-afternoon
```

Runs the Conductor's automatic iteration loop:
1. Reads the spec and confirms intent
2. Generates the composition
3. Evaluates quality across structure, melody, and harmony (10 metrics, quality score 1-10)
4. Adapts the spec if metrics fail and regenerates
5. Shows final output with evaluation summary

You can also compose from natural language:
```
/compose "an epic orchestral piece, dramatic, 2 minutes"
```

### `/critique` — Get honest feedback

```
/critique rainy-afternoon
```

The adversarial critic finds every weakness — it never praises. YaO includes 35 structured critique rules across 12 categories (structural, melodic, harmonic, rhythmic, arrangement, emotional, genre fitness, memorability, surprise, hook, groove, acoustic, conversation). Each rule emits `Finding` objects with severity (critical/major/minor/suggestion), evidence, bar-level location, and concrete recommendations. Writes `critique.md` to the iteration directory.

### `/regenerate-section` — Fix one section

```
/regenerate-section rainy-afternoon bridge
```

Regenerates only the specified section while keeping everything else intact. Creates a new iteration and shows a diff of what changed.

### `/explain` — Trace any decision

```
/explain why is there an F# in bar 12 of rainy-afternoon?
```

Queries the provenance log to show the chain of decisions that led to a specific note, chord, or structural choice.

### `/render` — MIDI to audio

```
/render rainy-afternoon
```

Renders the latest iteration to WAV using FluidSynth.

### `/arrange` — Transform an existing piece

```
/arrange rainy-afternoon --style jazz
```

Applies transformations like reharmonization, regrooving, or reorchestration using the arrangement engine with style vector transfer and preservation contracts.

---

## Method 3: Direct CLI (maximum control)

For precise control, use the CLI commands directly:

```bash
# Create project
yao new-project my-song

# Generate with automatic iteration (recommended)
yao conduct --spec specs/projects/my-song/composition.yaml --project my-song

# Or generate from natural language
yao conduct "a jazz ballad for late night, 2 minutes"

# Single-pass generation (no iteration)
yao compose specs/projects/my-song/composition.yaml

# Regenerate just one section
yao regenerate-section my-song bridge --seed 99

# Compare two variations
yao diff specs/projects/my-song/composition.yaml --seed-a 1 --seed-b 42

# Understand why a note was generated
yao explain specs/projects/my-song/composition.yaml --query melody

# Validate a spec without generating
yao validate specs/projects/my-song/composition.yaml

# Render MIDI to WAV (requires FluidSynth)
yao render outputs/projects/my-song/iterations/v001/full.mid
```

---

## Typical Session

Here's a complete session using Claude Code:

```
You: /sketch
     "Background music for a puzzle game. Minimal, slightly mysterious,
      looping-friendly. About 60 seconds."

Claude: I'd suggest:
        Key: A minor (mysterious feel)
        Tempo: 95 BPM (calm but engaged)
        Instruments: piano (melody), synth_pad_warm (pad)
        Sections: intro (4 bars, pp) -> loop_a (8 bars, mp) -> loop_b (8 bars, mf) -> outro (4 bars, pp)
        Generator: stochastic (seed 7, temperature 0.4)

        Would you like to adjust anything?

You: Make it a bit faster, 110 BPM. Add a vibraphone for the melody instead of piano.

Claude: Updated. Writing spec... Validated. Run /compose puzzle-bgm to generate.

You: /compose puzzle-bgm

Claude: [Runs Conductor with automatic iteration]
        Generated 78 notes across vibraphone, synth_pad_warm
        Duration: 52.4s
        All 8 evaluation metrics PASS
        Output: outputs/projects/puzzle-bgm/iterations/v001/

You: /critique puzzle-bgm

Claude: [Writes critique.md]
        MINOR: Vibraphone melody in bars 8-12 lacks contour variety
        SUGGESTION: Loop transition (bar 12->13) could use a fill

        Want to fix something? Use /regenerate-section puzzle-bgm loop_a

You: /regenerate-section puzzle-bgm loop_a

Claude: [Regenerates only loop_a with new seed, preserves everything else]
        New iteration at v002. Diff:
        Modified: 23 notes, Added: 5, Removed: 3
        Contour variety improved (0.35 -> 0.52)
```

---

## The Orchestra: 7 Subagents

Behind the scenes, Claude Code can invoke specialized subagents:

| Subagent | Role |
|---|---|
| **Producer** | Coordinates all subagents, resolves conflicts, makes final decisions |
| **Composer** | Generates melodies, motifs, themes, and structural outlines |
| **Harmony Theorist** | Designs chord progressions, modulations, cadences |
| **Rhythm Architect** | Creates drum patterns, grooves, syncopation, fills |
| **Orchestrator** | Assigns instruments, voicings, frequency spacing |
| **Mix Engineer** | Manages stereo placement, dynamics, frequency balance |
| **Adversarial Critic** | Finds weaknesses — never praises |

---

## Domain Skills

YaO includes 44 domain knowledge skills that Claude Code can draw on:

| Category | Skills |
|---|---|
| Genres (29) | cinematic, jazz_swing, jazz_ballad, rock_classic, pop, pop_western, pop_japan, electronic (edm_house, synthwave), ambient, deep_house, lo_fi_hiphop, funk, blues, hiphop, baroque, romantic, orchestral_classical, neoclassical, acoustic_folk, game_8bit_chiptune, game_bgm_rpg, film_score_dramatic, bossa_nova, celtic_traditional, arab_maqam, indian_classical_hindustani, j_pop |
| Cultures (3) | Japanese, Middle Eastern, Indian Classical |
| Theory (4) | Voice leading, Microtonal, Process music, Twelve-tone |
| Instruments (1) | Piano |
| Psychology (2) | Tension-resolution, Emotion mapping |
| Articulation (4) | Jazz microtiming, Piano pedaling, Strings articulation, Winds articulation |

---

## Output Files

Each composition creates:

```
outputs/projects/<name>/iterations/v001/
+-- full.mid           # Complete MIDI -- open in any MIDI player
+-- stems/             # Per-instrument MIDI
|   +-- piano.mid
|   +-- acoustic_bass.mid
+-- analysis.json      # Note counts, pitch range, lint results
+-- evaluation.json    # Quality scores (6 dimensions: structure, melody, harmony, aesthetic, arrangement, acoustics)
+-- perceptual.json    # Acoustic analysis (LUFS, spectral features, onset density)
+-- provenance.json    # Why every decision was made
+-- critique.md        # Adversarial critique (if /critique was run)
+-- audio.wav          # Rendered audio (if --render-audio or /render was used)
```
