# /regenerate-section — Regenerate a specific section of a composition

## Purpose
Re-generate only a specific section (e.g., chorus, bridge) while keeping the rest intact. Creates a new iteration with the merged result.

## Arguments
- `$ARGUMENTS` — Project name and section name (e.g., "my-song chorus")

## Protocol

### Step 1: Parse arguments
Split `$ARGUMENTS` into project name and section name. If only one word is given, ask which section to regenerate.

### Step 2: Verify project exists
Check that `specs/projects/<project>/composition.yaml` exists and that `outputs/projects/<project>/iterations/` has at least one iteration.

### Step 3: Show current state
Read the latest `evaluation.json` and `analysis.json` to show:
- Which sections exist and their note counts
- Which evaluation metrics are currently failing
- The current section's contribution to any failures

### Step 4: Gather feedback
Ask the user: "What should change about the <section>? (e.g., more energy, different melody, slower tempo for this section, different seed)"

### Step 5: Run regeneration
```bash
yao regenerate-section <project> <section> [--seed N]
```

If the user requested a specific seed, pass `--seed N`. Otherwise, the tool automatically uses a different seed.

### Step 6: Show results
1. Display the new analysis and evaluation summaries
2. Show which metrics improved or worsened vs the previous iteration
3. Tell the user: "New iteration saved to `outputs/projects/<project>/iterations/v<NNN>/`"

### Step 7: Offer next steps
- "Happy with this? You can now `/critique <project>` for a full review."
- "Want to try again? Just say which section to regenerate."
- "To render audio: `yao render outputs/projects/<project>/iterations/v<NNN>/full.mid`"

## Subagents Used
- **Composer**: Generates the new section content
- **Producer**: Decides on merge strategy and evaluates result
