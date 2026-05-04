# /conduct — Natural language composition with feedback loop

Run YaO's full Conductor pipeline from a natural language description. This is the fastest path from an idea to music.

**Input:** `$ARGUMENTS` — A natural language description of the desired music.

## Execute:

### Phase 1 — Intent Crystallization

1. Parse the user's description to extract musical intent:
   - Mood / emotion keywords
   - Instrumentation preferences
   - Genre hints
   - Duration / tempo / key if specified
2. Display the extracted intent and ask for confirmation:
   > "I understood: [extracted intent]. Shall I proceed, or would you like to refine?"

### Phase 2 — Spec Construction

3. Run the Conductor with the confirmed description:
```bash
yao conduct "$ARGUMENTS" --iterations 3
```

This internally:
- Builds a CompositionSpec via SpecCompiler (keyword extraction → spec)
- Plans the form and harmony (CPIR)
- Generates notes via the selected strategy
- Evaluates against metrics
- Runs adversarial critique
- Adapts and regenerates if needed (up to max iterations)

### Phase 3 — Results

4. Display the Conductor result:
   - Number of iterations taken
   - Quality score and pass rate
   - Adaptations applied (if any)
   - File locations (MIDI, stems, evaluation, provenance)

5. Offer next steps:
   - "Want to hear it? I can render to audio with `/render`"
   - "Want to improve a section? Use `/regenerate-section <project> <section>`"
   - "Want a detailed critique? Use `/critique <project>`"
   - "Want full control? Use `/sketch` to build a YAML spec interactively"

## Important

- Do NOT skip from description directly to note generation.
- The 6-phase protocol (PROJECT.md Section 6) is enforced by the Conductor internally.
- Every decision is recorded in provenance.json.

## Subagents Used
- **Producer**: Coordination, spec approval
- **Spec Compiler**: NL → CompositionSpec
- **Composer**: Melody and structure
- **Adversarial Critic**: Post-generation critique
