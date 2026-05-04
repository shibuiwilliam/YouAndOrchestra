# /feedback — Natural-language feedback translated to structured suggestions

## Purpose
Accept natural-language feedback about a generated piece and translate it into structured suggestions for regeneration.

## Arguments
- `$ARGUMENTS` — Project name, iteration, and feedback text in quotes

## Protocol

### Step 1: Parse arguments
Extract project name, iteration, and the quoted feedback text.

### Step 2: Verify project and iteration exist
Check that `specs/projects/<project>/` and the specified iteration exist.

### Step 3: Translate feedback
Use `NLFeedbackTranslator.translate()` to convert the NL text into a `StructuredFeedback` object with:
- Target sections (detected from text)
- Target instruments (detected from text)
- Intents (matched from phrase table)
- Parameter adjustments
- Preserved aspects

### Step 4: Handle ambiguity
If the translator marks the feedback as ambiguous, show the ambiguity reason and suggest recognized phrases the user can try.

### Step 5: Save feedback
Persist the structured feedback to `outputs/projects/<project>/iterations/<iteration>/feedback.json`.

### Step 6: Show suggestions
Display the structured interpretation:
- What sections/instruments are targeted
- What changes are suggested
- What will be preserved
- Recommended next step (e.g., `/regenerate-section chorus --use-pins`)

## Example
```
/feedback my-song v003 "the chorus feels weak; I want more impact"
```

## Output
- `feedback.json` with structured suggestions
- Human-readable summary of proposed changes
