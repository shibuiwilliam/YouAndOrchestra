# /critique — Adversarial critique of a generated composition

Critically evaluate a composition's weaknesses. The critic does NOT praise — it finds problems.

**Input:** `$ARGUMENTS` — Project name and optional iteration (e.g., "my-song" or "my-song v001"). If no iteration specified, use the latest.

## Execute this protocol:

### Step 1: Locate the project
Parse project name and optional iteration from `$ARGUMENTS`. Find the iteration directory:
- If iteration specified (e.g., "v001"): use `outputs/projects/<name>/iterations/v001/`
- If not: find the latest iteration directory by listing `outputs/projects/<name>/iterations/` and picking the highest version number

### Step 2: Read the outputs
Read these files from the iteration directory:
- `evaluation.json` — structured quality scores per metric (pass/fail, score vs target)
- `analysis.json` — note counts, pitch range, lint results
- `provenance.json` — generation decisions and rationale

Also read `specs/projects/<name>/intent.md` if it exists.

### Step 3: Run evaluation if needed
If `evaluation.json` doesn't exist, run:
```bash
yao evaluate <project-name>
```

### Step 4: Structured critique from evaluation data
Read `evaluation.json` and analyze each failing metric:

**For each FAIL in evaluation.json:**
- State the metric name, actual score, target, and tolerance
- Explain what this means musically
- Provide a specific, actionable fix

### Step 5: Deep musical analysis across 5 dimensions

**Structural:** Is the form predictable? Is there enough contrast between sections? Are transitions abrupt or smooth? Reference the `section_contrast` metric from evaluation.json.

**Melodic:** Does the melody have a clear contour or is it directionless? Is it memorable? Are there too many repeated patterns? Reference `pitch_range_utilization`, `stepwise_motion_ratio`, and `contour_variety` metrics.

**Harmonic:** Are chord progressions functional or random? Is there harmonic variety? Any voice-leading issues? Reference `pitch_class_variety` and `consonance_ratio`.

**Rhythmic:** Is there rhythmic interest or just straight quarter notes? Does it groove? Any syncopation or rhythmic surprises?

**Emotional:** Does the composition match the intent.md? Is there an emotional arc or is it flat? Does the tension trajectory feel natural?

### Step 6: Write critique
Write a `critique.md` file to the iteration directory with:
- A severity header: counts of **critical** / **major** / **minor** / **suggestion** findings
- Each finding labeled with severity
- Specific bar and beat references where possible (from analysis.json)
- An actionable improvement direction for each finding
- A "Priority Fixes" section listing the top 3 most impactful changes

### Step 7: Suggest next steps
Based on the severity of findings:

**If critical issues exist:**
"These need to be fixed first. I recommend:
1. `/regenerate-section <project> <worst-section>` — to redo the weakest section
2. Adjust the spec (key, tempo, instruments) and re-run `/compose <project>`"

**If only minor issues:**
"The composition is solid. To refine:
1. Try a different seed for variety: edit the spec and set a different seed
2. Fine-tune the trajectory for better emotional arc
3. Use `/regenerate-section` on specific sections"

### Step 8: Compare with previous iterations (if available)
If there are multiple iterations, compare evaluation.json across versions:
- Show which metrics improved, worsened, or stayed the same
- Identify whether the Conductor's adaptations were effective

## Rules
- **Never say "this sounds good"** — finding problems is the job
- Be specific: "bars 12-16 melody descends monotonically" not "melody could improve"
- Reference intent.md when evaluating emotional alignment
- Every criticism must include a direction: what to try instead
- Use evaluation.json data for evidence-based critique, not speculation
