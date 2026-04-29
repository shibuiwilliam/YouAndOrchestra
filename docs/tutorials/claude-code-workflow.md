# Using YaO with Claude Code

YaO is designed to be used interactively through Claude Code. Here are the three ways to create music, from simplest to most control.

---

## Method 1: Just Ask (natural language)

Open Claude Code in the YaO directory and describe what you want:

> "Create a calm 90-second piano piece in D minor for studying. Build slowly to a gentle peak, then fade out."

Claude Code will:
1. Create a project with `yao new-project`
2. Write a composition spec matching your description
3. Run `yao compose` to generate MIDI
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
- Instrument selection
- Section structure (intro/verse/chorus/outro)
- Dynamic arc
- Writes the YAML spec for you

### `/compose` — Generate from a spec

```
/compose rainy-afternoon
```

Follows the 6-phase protocol:
1. **Intent** — Confirms what the piece should feel like
2. **Trajectory** — Proposes tension/density curves
3. **Generate** — Runs the generator, writes MIDI + stems
4. **Critique** — Reviews the output for weaknesses
5. **Iterate** — Offers to adjust and regenerate
6. **Deliver** — Shows final output location

### `/critique` — Get honest feedback

```
/critique rainy-afternoon
```

The adversarial critic finds every weakness — it never praises. Each finding includes severity, specific bar references, and a suggestion for improvement.

### `/compose` again — Iterate based on feedback

```
/compose rainy-afternoon
```

Each run creates a new version (v001 → v002 → v003), so you never lose previous iterations.

---

## Method 3: Direct CLI (maximum control)

For precise control, use the CLI commands directly:

```bash
# Create project
yao new-project my-song

# Generate (rule-based, deterministic)
yao compose specs/projects/my-song/composition.yaml

# Generate with stochastic variation
# (edit composition.yaml to add: generation: {strategy: stochastic, seed: 42, temperature: 0.7})
yao compose specs/projects/my-song/composition.yaml

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
        Sections: intro (4 bars, pp) → loop_a (8 bars, mp) → loop_b (8 bars, mf) → outro (4 bars, pp)
        Generator: stochastic (seed 7, temperature 0.4)
        
        Would you like to adjust anything?

You: Make it a bit faster, 110 BPM. Add a vibraphone for the melody instead of piano.

Claude: Updated. Writing spec... Validated. Run /compose puzzle-bgm to generate.

You: /compose puzzle-bgm

Claude: [Runs 6-phase protocol, shows analysis]
        Generated 78 notes across vibraphone, synth_pad_warm
        Duration: 52.4s
        All 8 evaluation metrics PASS
        Output: outputs/projects/puzzle-bgm/iterations/v001/

You: /critique puzzle-bgm

Claude: [Writes critique.md]
        MINOR: Vibraphone melody in bars 8-12 lacks contour variety
        SUGGESTION: Loop transition (bar 12→13) could use a fill
        
        To iterate: adjust the spec and run /compose puzzle-bgm again.

You: Let's try a different seed for more variety.

Claude: [Updates seed to 23, runs /compose again]
        New iteration at v002. Here's the diff:
        Modified: 45 notes, Added: 12, Removed: 8
```

---

## Output Files

Each composition creates:

```
outputs/projects/<name>/iterations/v001/
├── full.mid           # Complete MIDI — open in any MIDI player
├── stems/             # Per-instrument MIDI
│   ├── piano.mid
│   └── acoustic_bass.mid
├── analysis.json      # Note counts, pitch range, lint results
└── provenance.json    # Why every decision was made
```
