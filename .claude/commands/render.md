# /render — Render MIDI to audio and score

## Purpose
Convert a MIDI file to WAV audio using SoundFont rendering.

## Arguments
- `$ARGUMENTS` — Project name and iteration, or path to MIDI file

## Protocol

1. **Locate the MIDI file**: Find full.mid in the specified iteration
2. **Run audio rendering**: `yao render <midi_path> --soundfont <sf_path>`
3. **Report results**: File path, duration, file size
4. **Handle errors**: If fluidsynth is unavailable, explain how to install it

## Uses
- Subagent: Mix Engineer
