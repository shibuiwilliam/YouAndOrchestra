# /cover-art — Generate album cover art for a composition

## Purpose
Generate visually striking album cover art that matches a composition's musical character using Google Gemini image generation.

## Arguments
- `$ARGUMENTS` — Path to a composition YAML spec, or a project name

## Protocol

1. **Locate the spec file**:
   - If `$ARGUMENTS` is a file path, use it directly
   - If it's a project name, look for `specs/projects/$ARGUMENTS/composition.yaml`
   - Read the spec and display a summary: title, genre, mood, tempo, key, instruments

2. **Check prerequisites**:
   - Verify `GEMINI_API_KEY` environment variable is set
   - Verify `google-genai` package is installed (`pip install -e ".[cover-art]"`)
   - If either is missing, explain the setup steps and stop

3. **Confirm options with the user**:
   - Ask if they want a specific visual style (e.g., "watercolor", "minimalist", "abstract expressionist")
   - Ask if they want to override the mood
   - Ask where to save the output (default: `outputs/projects/<name>/cover.png`)

4. **Generate the cover art**:
   ```bash
   yao cover-art <spec_path> [--style "<style>"] [--mood "<mood>"] [-o <output_path>]
   ```

5. **Report results**:
   - Display the output path
   - Show the prompt that was used (for reproducibility)
   - If the generation failed, explain the error and suggest fixes

6. **Offer next steps**:
   - "Want a different style? Re-run with `--style` to try another look."
   - "To render audio alongside: `/render <project>`"

## Options

| Option | Default | Description |
|---|---|---|
| `--output`, `-o` | `outputs/projects/<name>/cover.png` | Output image path |
| `--style` | (none) | Visual style hint (e.g., "watercolor", "minimalist") |
| `--mood` | (from spec) | Override mood for the artwork |
| `--model` | `gemini-2.0-flash-exp` | Gemini model to use |

## Setup

If not already configured:
1. Get a Google API key at https://aistudio.google.com/apikey
2. `export GEMINI_API_KEY="your-key-here"`
3. `pip install -e ".[cover-art]"`

## Uses
- Skill: cover-art
