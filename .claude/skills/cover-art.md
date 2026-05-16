---
name: cover-art
description: Generate album cover art for a composition using Google Gemini image generation (Nano Banana)
triggers:
  - cover art
  - album art
  - artwork
  - cover image
  - album cover
requires:
  env: GOOGLE_API_KEY
  package: google-genai
---

# Cover Art Generation

Generate visually striking album cover art that matches a composition's musical character.

## How It Works

The cover art generator reads a composition's metadata (genre, mood, tempo, key, instruments) and translates musical characteristics into visual language for Google's Gemini image generation API.

### Musical → Visual Translation

| Musical Feature | Visual Interpretation |
|---|---|
| Genre (jazz) | Smoky nightclub, warm golden lighting, abstract shapes |
| Genre (electronic) | Neon lights, futuristic geometry, digital aesthetic |
| Genre (classical) | Elegant oil painting style, ornate golden frames |
| Genre (ambient) | Ethereal misty landscapes, soft gradients |
| Genre (metal) | Dark dramatic imagery, sharp angles |
| Minor key | Cool color palette, darker tones |
| Major key | Warm color palette, brighter tones |
| Slow tempo (<80 BPM) | Calm, contemplative energy |
| Fast tempo (>150 BPM) | Dynamic, intense movement |

## CLI Usage

```bash
# Basic — generates cover.png next to the spec
yao cover-art specs/templates/genres/jazz/bebop-standard.yaml

# With style override
yao cover-art my-project/composition.yaml --style "watercolor painting"

# With mood and custom output path
yao cover-art specs/templates/lofi-cafe.yaml --mood "nostalgic" -o artwork/cover.png

# Using a different model
yao cover-art spec.yaml --model gemini-2.0-flash-exp
```

## Setup

1. Get a Google API key at https://aistudio.google.com/apikey
2. Set the environment variable:
   ```bash
   export GOOGLE_API_KEY="your-key-here"
   ```
3. Install the dependency:
   ```bash
   pip install -e ".[cover-art]"
   ```

## Programmatic API

```python
from yao.render.cover_art import CoverArtRequest, generate_cover_art
from pathlib import Path

request = CoverArtRequest(
    title="Midnight Jazz",
    genre="jazz_bebop",
    mood="smoky, intimate",
    instruments=("saxophone", "piano", "contrabass"),
    tempo_bpm=160.0,
    key="Bb minor",
    style_hint="abstract expressionist painting",
)

result = generate_cover_art(request, Path("output/cover.png"))
if result.success:
    print(f"Saved to: {result.image_path}")
else:
    print(f"Error: {result.error_message}")
```

## Options

| Option | Default | Description |
|---|---|---|
| `--output`, `-o` | `cover.png` next to spec | Output image path |
| `--style` | (none) | Visual style hint (e.g., "watercolor", "minimalist") |
| `--mood` | (from spec) | Override mood for the artwork |
| `--model` | `gemini-2.0-flash-exp` | Gemini model to use |

## Notes

- Generated images are square (1:1 aspect ratio)
- No text/letters are generated in the image (clean artwork)
- The prompt is logged in provenance for reproducibility
- Images include a SynthID watermark (Gemini standard)
- Falls back gracefully if API key is missing or service is unavailable
