# Development Roadmap

## Value-Driven Milestones

### Milestone 1: "Describe and Hear" (current)
**User value:** Describe what you want in YAML, generate it, hear it.

**Delivered:**
- CLI compose pipeline (spec → generate → MIDI → stems → analysis → evaluation)
- Rule-based and stochastic generators with seed/temperature control
- 4 spec templates (minimal, bgm-90sec, cinematic-3min, trajectory-example)
- Trajectory-driven dynamics (tension curves shape velocity)
- Auto-versioned iterations (v001, v002, ...)
- Full provenance tracking

**Next:**
- Instant MIDI playback preview (`yao preview`)
- Strudel pattern emitter for browser-based playback
- Example projects with pre-generated output in `gallery/`

### Milestone 2: "Iterate and Improve"
**User value:** Tell YaO what you don't like, and it improves.

**Delivered:**
- Score diff with modified note tracking
- CLI diff and explain commands
- Quality evaluation across structure/melody/harmony

**Next:**
- Section-level regeneration (keep rest, regenerate one section)
- Feedback-driven refinement loop via `/critique` → `/regenerate-section`
- Session/Project Runtime layer for stateful iteration

### Milestone 3: "Richer Music"
**User value:** Music sounds professional with proper harmony, rhythm, dynamics.

**Delivered:**
- Harmony IR (Roman numeral chord functions, realize(), diatonic quality)
- Motif transformations (transpose, invert, retrograde, augment)
- Voice leading checks (parallel fifths/octaves, voice distance)
- Constraint system (must/must_not/prefer/avoid with scoped rules)
- Walking bass patterns, syncopation, dotted rhythms

**Next:**
- Negative space enforcement in generators
- More chord progression variety (secondary dominants, modulation)
- Multi-octave voice leading optimization
- Markov chain and constraint solver generators

### Milestone 4: "My Style"
**User value:** YaO learns your preferences and produces music in your taste.

**Next:**
- Reference library matching (positive/negative references)
- Spec fragments and composability (extends/overrides in YAML)
- Style profile persistence
- Arrangement mode (reharmonize, regroove, reorchestrate)

### Milestone 5: "Production Ready"
**User value:** Use YaO output in a real project.

**Next:**
- DAW integration (Reaper MCP)
- LilyPond/MusicXML score export
- Mix engineer pipeline (EQ, compression, spatial)
- Multi-format export (stems, MusicXML, LilyPond, Strudel)

## Technical Roadmap

### Phase: Generator Evolution
1. Markov chain generator (probabilistic transitions from corpus)
2. Constraint solver generator (backtracking search with constraints)
3. AI bridge generator (external model integration via API)

### Phase: Agent Protocol
1. Abstract `AgentProtocol` in Python code (backend-agnostic)
2. Claude Code adapter (maps protocol to .claude/agents/)
3. Session runtime with generation cache and feedback queue

### Phase: Perception Layer
1. Reference feature extraction (spectral, rhythmic, harmonic)
2. Similarity scoring between generated and reference works
3. Style vector computation for interpolation
