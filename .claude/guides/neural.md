# Neural Integration Guide

## Architecture

Neural generators live in `src/yao/generators/neural/`. This is the ONLY
location where `torch`, `transformers`, `audiocraft`, and `magenta` may
be imported.

## Installation

```bash
# Core YaO (no neural)
pip install yao

# With neural backends
pip install yao[neural]

# Or manually
pip install torch>=2.0 transformers>=4.40
```

## Provenance Contract

Every neural generation call MUST record these 5 fields:

| Field | Example |
|---|---|
| `model_version` | `"stable_audio_open_torch_2.3.0"` |
| `prompt` | `"warm analog synth pad, slow attack"` |
| `seed` | `42` |
| `output_hash` | `"sha256:abc123..."` |
| `rights_status` | `"model_license_stable_audio_open"` |

`rights_status="unknown"` triggers a warning. Never silently proceed.

## GPU vs CPU

| Mode | Speed | Quality |
|---|---|---|
| GPU (CUDA) | 5-15s for 30s audio | Full quality |
| CPU | 30-60s for 30s audio | Same quality, slower |
| Mock (testing) | <1s | Placeholder noise |

## Rights Status Values

| Value | Meaning |
|---|---|
| `model_license_stable_audio_open` | Stable Audio Open License |
| `model_license_musicgen` | Meta MusicGen License |
| `user_owned` | User provided their own model |
| `unknown` | WARNING — must be resolved |

## AI Disclosure

The `ai-disclosure-stamp` hook writes metadata to output files:
- "Generated with YaO v2.0"
- Model name and version
- Generation prompt (for transparency)

## Testing

- All tests use mocks (no GPU required)
- `pytest.mark.requires_neural` for tests needing actual backends
- CI runs mock-only tests
