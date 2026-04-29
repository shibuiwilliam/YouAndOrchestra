# /sketch — Interactive sketch-to-spec dialogue

Transform a musical idea into a complete YAML specification through guided dialogue.

**Input:** `$ARGUMENTS` — Optional initial description of the desired music. If empty, ask the user to describe what they want.

## Execute this protocol:

### Step 1: Gather Intent
If `$ARGUMENTS` is provided, use it as the starting description. Otherwise ask:
"Describe the music you want. Include any of these you have in mind: mood, use case (game, film, study), duration, instruments, style."

### Step 2: Choose Project Name
Ask: "What should we call this project?" Use the answer to create the project:
```bash
yao new-project <name>
```

### Step 3: Propose Spec
Based on the description, propose concrete values. Present them as a filled-in spec and ask for confirmation:

"Here's what I'd suggest based on your description:

- **Key:** D minor (melancholic feel)
- **Tempo:** 72 BPM (slow, contemplative)
- **Time signature:** 4/4
- **Instruments:** piano (melody), cello (bass), strings_ensemble (pad)
- **Sections:** intro (8 bars, pp) → verse (16 bars, mp) → chorus (8 bars, f) → outro (8 bars, pp)
- **Generator:** stochastic (seed 42, temperature 0.6)

Would you like to adjust anything? I can change instruments, tempo, key, dynamics, or section structure."

Use the following references for suggestions:
- Moods → keys: happy=C major, sad=D minor, calm=F major, dark=C minor, epic=D minor, mysterious=A minor
- Paces → tempo: slow/calm=80, moderate=100, fast/energetic=140
- Instrument keywords: "piano", "strings", "orchestra", "guitar", "synth", "ambient", "cinematic", "jazz", "classical"
- See `src/yao/constants/instruments.py` for all 46 available instruments

### Step 4: Propose Trajectory
"I'd suggest this emotional arc:
- Tension starts low (0.2), builds through the verse to 0.7, peaks in the chorus at 0.9, then settles to 0.2
- Density mirrors tension — sparse intro, full chorus, quiet outro

Should I create this trajectory, or adjust the shape?"

### Step 5: Write Files
Write `composition.yaml` with the agreed spec to `specs/projects/<name>/composition.yaml`.
Write `trajectory.yaml` if agreed.
Write `intent.md` with the original description crystallized to 1-3 sentences.

Validate the spec:
```bash
yao validate specs/projects/<name>/composition.yaml
```

### Step 6: Generate
"Your project is ready! Generating now..."

Run the composition:
```bash
yao conduct --spec specs/projects/<name>/composition.yaml --project <name> --iterations 3
```

### Step 7: Review and iterate
After generation completes:
1. Show the evaluation summary
2. If metrics failed, offer: "Want me to `/critique <name>` for detailed analysis?"
3. If specific sections are weak: "The <section> could be stronger. Want me to `/regenerate-section <name> <section>`?"
4. If all passed: "The composition looks solid! Want to hear it? I can render with `yao render <path>`."

## Complete Workflow Loop
```
/sketch → (builds spec) → /compose → (generates) → /critique → (finds issues) → /regenerate-section → (fixes) → /critique → ...
```

## Rules
- Offer concrete suggestions, not open-ended questions ("D minor or F minor?" not "what key?")
- Always validate the YAML before generating
- Explain musical choices briefly ("D minor because you said melancholic")
- After successful generation, always offer the next workflow step
