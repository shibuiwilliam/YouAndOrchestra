# Audio Rendering Setup

YaO generates MIDI by default. To render MIDI to WAV audio, you need [FluidSynth](https://www.fluidsynth.org/) and a SoundFont file.

## Install FluidSynth

```bash
# macOS
brew install fluid-synth

# Ubuntu/Debian
sudo apt-get install fluidsynth

# Verify
fluidsynth --version
```

## Get a SoundFont

Download [FluidR3_GM](https://member.keymusician.com/Member/FluidR3_GM/index.html) (~140 MB) and place it in the `soundfonts/` directory:

```
soundfonts/FluidR3_GM.sf2
```

## Render

```bash
yao render outputs/projects/my-song/iterations/v001/full.mid
```

Or render during composition:

```bash
yao compose my-spec.yaml --render-audio
```

!!! note
    Audio rendering is optional. YaO works fully with MIDI output only. If FluidSynth is not installed, the `--render-audio` flag will show a clear error message with install instructions.
