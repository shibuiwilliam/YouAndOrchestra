#!/usr/bin/env bash
# Post-generate render hook for YaO
# Automatically renders MIDI to audio and notation after generation completes.
# Triggered: after any generation step produces a new iteration.

set -euo pipefail

MIDI_PATH="${1:-}"

if [ -z "$MIDI_PATH" ]; then
    echo "Usage: post-generate-render.sh <path-to-full.mid>"
    exit 1
fi

if [ ! -f "$MIDI_PATH" ]; then
    echo "MIDI file not found: $MIDI_PATH"
    exit 1
fi

ITER_DIR="$(dirname "$MIDI_PATH")"

echo "=== Post-generate: Rendering audio ==="

# Render to WAV (requires SoundFont)
if command -v fluidsynth &>/dev/null; then
    yao render "$MIDI_PATH" --output "$ITER_DIR/audio.wav" || echo "Audio render skipped (no SoundFont)"
else
    echo "FluidSynth not available — skipping audio render"
fi

echo "=== Post-generate render complete ==="
