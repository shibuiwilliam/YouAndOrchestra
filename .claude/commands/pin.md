# /pin — Attach localized feedback to a specific position

## Purpose
Attach a user comment to a specific (section, bar, beat, instrument) position in a generated piece. Pins drive targeted regeneration without changing the full spec.

## Arguments
- `$ARGUMENTS` — Project name, iteration, and pin details

## Protocol

### Step 1: Parse arguments
Extract project name, iteration (e.g., "v003"), location, and note from arguments.
Location format: `section:chorus,bar:6,beat:3,instrument:piano`

### Step 2: Verify project and iteration exist
Check that `specs/projects/<project>/` and the specified iteration exist.

### Step 3: Parse pin note into intent
Use `NLFeedbackTranslator.translate_pin_note()` to derive the user_intent from the note text.

### Step 4: Create pin
Create a `Pin` object with a unique id (pin-NNN), the parsed location, note, and intent.

### Step 5: Append to pins.yaml
Load or create `specs/projects/<project>/pins.yaml`, append the new pin, save.
Pins are immutable — never modify existing pins.

### Step 6: Mark iteration stale
Note that the current iteration has pending feedback that hasn't been applied yet.

### Step 7: Report
Show the created pin with its derived intent and affected region.

## Example
```
/pin my-song v003 --location "section:chorus,bar:6,beat:3,instrument:piano" --note "this dissonance is too harsh"
```

## Output
- Updated `pins.yaml`
- Summary of pin id, location, derived intent, affected bar range
