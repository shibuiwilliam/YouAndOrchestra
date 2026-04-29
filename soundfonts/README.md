# SoundFonts

YaO uses SoundFont (.sf2) files for audio rendering. These are not included in the repository due to their size.

## Recommended: FluidR3_GM

FluidR3_GM is a free General MIDI SoundFont (~140MB).

**Download:** https://member.keymusician.com/Member/FluidR3_GM/index.html

Place the file as: `soundfonts/FluidR3_GM.sf2`

## macOS with Homebrew

```bash
brew install fluid-synth
# FluidSynth typically installs a default SoundFont
```

## Rendering

Audio rendering requires `fluidsynth` to be installed on your system. Without it, YaO will still generate MIDI files but cannot render to WAV.

```bash
# macOS
brew install fluid-synth

# Ubuntu/Debian
sudo apt-get install fluidsynth

# Verify
fluidsynth --version
```
