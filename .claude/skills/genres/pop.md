---
genre_id: pop
display_name: "Pop"
parent_genres: [rock, soul]
related_genres: [synth_pop, electro_pop, indie_pop, pop_western, pop_japan]
typical_use_cases: [commercial_music, radio_friendly, advertising, upbeat_background]
ensemble_template: custom
default_subagents:
  active: [composer, rhythm_architect, sound_designer, mix_engineer, adversarial_critic, producer]
  inactive: [harmony_theorist, loop_architect]
---

# Pop — Genre Skill

## Defining Characteristics
- Tempo: 95-135 BPM (sweet spot 110-125)
- Straight eighth-note feel; light swing acceptable in some sub-genres
- Hook-driven: melodic hooks, rhythmic hooks, and lyrical hooks are the core currency
- Simple, repetitive harmony: typically 3-5 chords cycling throughout
- Verse-chorus form with clear section contrast
- Vocal melody is the primary focus; all other elements serve the vocal
- Polished production with layered textures
- Four-on-the-floor or backbeat-driven rhythms
- Bright, present mix with controlled dynamics
- Earworm factor: melodies designed for memorability and singability

## Required Spec Patterns
```yaml
tempo_bpm: 118
time_signature: "4/4"
swing: 0.0
instruments:
  - name: synth_pad
    role: harmony
  - name: synth_bass
    role: bass
  - name: drums
    role: rhythm
  - name: vocals
    role: melody
generation:
  strategy: phrase_aware
  temperature: 0.3
features:
  chord_aware_melody: true
  voice_leading_optimization: true
```

## Idiomatic Chord Progressions
- I-V-vi-IV (the "four-chord" progression, ~30%)
- vi-IV-I-V (rotation of the above, ~20%)
- I-IV-vi-V (bright variant, ~15%)
- I-vi-IV-V (doo-wop / 50s pop, ~10%)
- I-V-ii-IV (modern pop, ~10%)
- vi-V-IV-V (minor pop, ~8%)
- I-iii-vi-IV (melancholic pop, ~7%)

## Idiomatic Rhythms
```
KICK:   X . . . X . . . X . . . X . . .
SNARE:  . . . . X . . . . . . . X . . .
HIHAT:  X . X . X . X . X . X . X . X .
```
- Four-on-the-floor kick or sparse pattern
- Snare on 2 and 4 (or clap layer)
- Hi-hat: straight eighths or sixteenths
- Percussion layers: shaker, tambourine, snap for texture
- Programmed drums common; live drums in organic pop

## Anti-Patterns
- Overly complex harmony (extended chords, chromatic movement feel out of place)
- Long instrumental passages without a vocal hook or melodic hook
- Dense, thick arranging that buries the melody (clarity is paramount)
- Excessive improvisation (pop is composed, not improvised)
- Dark or muddy production (pop should be bright and present)
- Irregular phrase lengths (4- and 8-bar regularity is the norm)
- Missing a hook (every section needs a memorable element)
- Severity: HIGH for buried melody and missing hooks; MEDIUM for complex harmony

## Reference Tracks
- None yet (rights-cleared pop references needed)

## Default Sound Design
```yaml
instruments:
  synth_pad: { synthesis: { kind: subtractive, waveform: saw, filter_cutoff_hz: 2000 }, effect_chain: [{ type: chorus, rate: 0.5, depth: 0.3 }, { type: reverb, room_size: 0.5, wet: 0.25 }] }
  synth_bass: { synthesis: { kind: subtractive, waveform: square, filter_cutoff_hz: 800 }, effect_chain: [{ type: compressor, threshold_db: -12, ratio: 4 }] }
  drums: { synthesis: { kind: sample_based, pack: "pop_kit_modern" }, effect_chain: [{ type: compressor, threshold_db: -10, ratio: 5 }] }
```

## Evaluation Weight Adjustments
structure.section_contrast: 1.4
melody.contour_variety: 1.0
melody.hook_memorability: 1.5
melody.chord_tone_targeting: 1.0
harmony.consonance_ratio: 1.3
harmony.voice_leading: 0.8
rhythm.groove_consistency: 1.3
arrangement.texture_density_evolution: 1.2

## Default Trajectories
```yaml
trajectories:
  tension:
    type: arc
    sections: { intro: 0.2, verse_1: 0.4, pre_chorus: 0.6, chorus_1: 0.8, verse_2: 0.4, pre_chorus_2: 0.65, chorus_2: 0.85, bridge: 0.5, chorus_3: 0.9, outro: 0.3 }
  density:
    type: arc
    sections: { intro: 0.3, verse_1: 0.4, pre_chorus: 0.55, chorus_1: 0.75, verse_2: 0.45, pre_chorus_2: 0.6, chorus_2: 0.8, bridge: 0.5, chorus_3: 0.85, outro: 0.3 }
```

## Tempo
- Range: 95-135 BPM
- Sweet spot: 110-125 BPM (energetic but comfortable for singing)
- Ballad pop: 60-95 BPM
- Dance pop: 118-130 BPM
- Uptempo pop: 130-145 BPM
- Time feel: straight, locked, metronomic

## Key Preferences
- C major, G major (bright, accessible)
- A minor, E minor (melancholic pop)
- Eb major, Bb major (vocal-friendly, warm)
- Key changes up a half-step or whole-step for final chorus (classic pop modulation)
- Major keys dominate; minor keys for emotional or edgy tracks

## Drum Pattern Family
- Default: pop_four_on_floor or pop_backbeat
- Kick: four-on-the-floor or kick-snare alternation
- Snare/Clap: beats 2 and 4 without exception
- Hi-hat: straight eighths or sixteenths, open on & of 4
- Percussion: shaker, tambourine layered for texture
- Fills: simple, short, one-bar maximum at transitions

## Instrumentation Defaults
- Core: synth_pad or piano (harmony), synth_bass or electric_bass (bass), drums (rhythm)
- Melody: vocals (primary), synth_lead (hooks and counter-melodies)
- Common additions: acoustic_guitar (verse texture), strings (chorus lift), percussion layers
- Avoid: heavily distorted guitar (unless pop-rock), free jazz instruments, complex orchestral writing

## Section Structure
- Intro: 4-8 bars, establishing the hook or vibe
- Verse 1: 8-16 bars, storytelling, lower energy
- Pre-Chorus: 4-8 bars, building toward chorus (harmonic lift, rising melody)
- Chorus: 8-16 bars, maximum energy, the hook, the payoff
- Verse 2: 8-16 bars, continuing narrative, slight variation
- Chorus 2: repeat with possible added layers
- Bridge: 8 bars, contrast (new chord progression, different melody, stripped arrangement)
- Final Chorus: often double chorus or modulated up
- Outro: 4-8 bars, chorus fade or definitive ending

## Trajectory Patterns
- Classic Pop Arc: tension 0.2 -> 0.4 -> 0.6 -> 0.8 -> 0.4 -> 0.85 -> 0.5 -> 0.9 -> 0.3
- Dance Pop Build: tension 0.3 -> 0.5 -> 0.7 -> 0.9 -> 0.5 -> 0.95 -> 0.4
- Ballad Pop: tension 0.15 -> 0.3 -> 0.5 -> 0.7 -> 0.3 -> 0.75 -> 0.2

## Cadences
- V-I (standard resolution)
- IV-I (plagal, warm ending)
- vi-V-I (approach from relative minor)
- IV-V-I (classic pop full cadence)
- Chorus loop: progression repeats to fade (avoids final cadence entirely)

## Cliches to AVOID
- Overly complex harmony (keep it simple and singable)
- Long instrumental solos (the vocal is the star)
- Unpredictable phrase structures (4- and 8-bar units are expected)
- Dark, murky production (pop is bright and clear)
- Too many ideas (one hook per section is enough)
- No dynamic contrast between verse and chorus (the chorus must lift)
- Severity: HIGH = no hook, buried vocal melody; MEDIUM = irregular phrasing, overcomplication
- Fix recipe: simplify chord progression to 3-4 chords, add a clear melodic hook, ensure chorus is louder and fuller than verse

## Quality Heuristics
- Melody: stepwise motion with occasional leaps for emphasis, pentatonic-adjacent, singable range (one octave)
- Harmony: mostly diatonic, 3-5 chords cycling, consonant
- Bass: simple root-based patterns, octave jumps for energy
- Drums: tight, punchy, consistent groove with subtle fills
- Velocity: moderate to high (70-110), consistent within sections
- Production: polished, layered, bright top end, controlled low end
- Hook: must be identifiable within first 30 seconds

## Production Notes
- Target loudness: -10 to -7 LUFS (loud, polished, radio-ready)
- Vocals: center, compressed, bright EQ, reverb and delay
- Bass: center, sub-bass present but controlled
- Stereo: wide in chorus (doubled guitars, panned synths), narrower in verse
- Effects: reverb on vocals and snare, delay on vocal hooks
- Compression: heavy bus compression for glue

## References
- Burns, Gary. "A Typology of Hooks in Popular Records." *Popular Music* 6, no. 1 (1987): 1-20.
- Temperley, David. *The Musical Language of Rock*. Oxford University Press, 2018 (pop-rock overlap chapters).
- de Clercq, Trevor and David Temperley. "A Corpus Analysis of Rock Harmony." *Popular Music* 30, no. 1 (2011): 47-70.
- Covach, John. "Form in Rock Music." In *Engaging Music*, edited by D. Stein. Oxford University Press, 2005.
- Nobile, Drew. *Form as Harmony in Rock Music*. Oxford University Press, 2020.

## Use Cases
- Radio-friendly commercial music
- Advertising and branding
- Upbeat background for content
- Workout playlists (uptempo pop)
- Wedding and event music
- Singalong and karaoke contexts
