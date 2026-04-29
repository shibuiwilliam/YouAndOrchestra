# /compose — Generate music with the Conductor

Compose music using YaO's automated feedback loop. The Conductor handles generation, evaluation, adaptation, and iteration automatically.

**Input:** `$ARGUMENTS` — Either a project name, a path to composition.yaml, or a natural language description.

## Execute:

### If `$ARGUMENTS` looks like a natural language description (contains spaces, no file extension):

Run the Conductor directly from the description:
```bash
yao conduct "$ARGUMENTS"
```

This will:
1. Build a spec from the description (key, tempo, instruments, sections)
2. Generate → evaluate → adapt → regenerate (up to 3 iterations)
3. Output MIDI + stems + analysis + evaluation + provenance

### If `$ARGUMENTS` is a project name or spec path:

1. If it's a project name, look for `specs/projects/$ARGUMENTS/composition.yaml`
2. Read the spec file and display a summary to the user:
   - Title, key, tempo, time signature
   - Instruments and their roles
   - Sections with bar counts and dynamics
   - Generation strategy, seed, temperature
3. Ask: "Ready to generate? Any adjustments to the spec first?"
4. Run the Conductor:
```bash
yao conduct --spec <path-to-composition.yaml> --project $ARGUMENTS --iterations 3
```

### After generation:

1. Display the Conductor result summary (iterations, pass rate, adaptations)
2. Display the analysis summary (notes, instruments, duration, lint)
3. Display the evaluation summary (per-metric pass/fail)
4. Tell the user where the files are:
   - MIDI: `outputs/projects/<name>/iterations/v<NNN>/full.mid`
   - Stems: `outputs/projects/<name>/iterations/v<NNN>/stems/`
   - Evaluation: `outputs/projects/<name>/iterations/v<NNN>/evaluation.json`
   - Provenance: `outputs/projects/<name>/iterations/v<NNN>/provenance.json`

5. **If any metrics failed**, explain specifically:
   - Which metrics failed and by how much
   - What adaptations the Conductor tried (from the adaptation log)
   - Suggest targeted fixes:
     - For `section_contrast` failure: "Try `/regenerate-section <project> <section>` to improve the weak section"
     - For `pitch_range_utilization` failure: "The melody range is too narrow/wide. Adjust temperature or try a different seed."
     - For `stepwise_motion_ratio` failure: "Too many leaps/steps. Adjust temperature."
     - For `consonance_ratio` failure: "Too many dissonant intervals. Lower the temperature."

6. Ask: "Want to hear it? Open the MIDI file, or I can render to WAV with `yao render <path>`. To improve a specific section, use `/regenerate-section <project> <section>`."

### To iterate further:

If the user wants changes:
- For specific section issues: use `/regenerate-section <project> <section>`
- For spec-level changes: modify the composition.yaml and re-run `/compose <project>`
- For a full critique: run `/critique <project>`

Each run creates new iteration versions (v001 → v002 → v003).

## Subagents Used
- **Producer**: Overall coordination and decision-making
- **Composer**: Melody and structure generation
- **Harmony Theorist**: Chord progression evaluation
- **Adversarial Critic**: Weakness identification (post-generation)
