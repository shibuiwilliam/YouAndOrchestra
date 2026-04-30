# Development Roadmap

## Value-Driven Milestones

### Milestone 1: "Describe and Hear" -- COMPLETE
**User value:** Describe what you want in YAML, generate it, hear it.

**Delivered:**
- CLI compose pipeline (spec -> generate -> MIDI -> stems -> analysis -> evaluation)
- Rule-based and stochastic generators with seed/temperature control
- 4 spec templates (minimal, bgm-90sec, cinematic-3min, trajectory-example)
- Trajectory-driven dynamics (tension curves shape velocity)
- Auto-versioned iterations (v001, v002, ...)
- Full provenance tracking
- Example projects in specs/projects/

### Milestone 2: "Iterate and Improve" -- COMPLETE
**User value:** Tell YaO what you don't like, and it improves.

**Delivered:**
- Conductor feedback loop (generate -> evaluate -> adapt -> regenerate)
- Natural language composition via `yao conduct "<description>"`
- Section-level regeneration (keep rest, regenerate one section)
- Score diff with modified note tracking
- CLI diff, explain, conduct, and regenerate-section commands
- Quality evaluation across structure, melody, and harmony (10 metrics + quality score 1-10)
- Feedback-driven spec adaptation (9 metric-to-adaptation rules)
- MIDI reader (load existing MIDI back to ScoreIR for analysis)
- Evaluation report persistence (evaluation.json)
- 7 Claude Code slash commands with full workflow integration
- 7 subagent definitions for specialized roles

### Milestone 3: "Richer Music" -- IN PROGRESS
**User value:** Music sounds professional with proper harmony, rhythm, dynamics.

**Delivered:**
- Harmony IR (Roman numeral chord functions, realize(), diatonic quality)
- Motif transformations (transpose, invert, retrograde, augment, diminish)
- Voice leading checks (parallel fifths/octaves, voice distance)
- Constraint system (must/must_not/prefer/avoid with scoped rules)
- Walking bass patterns, syncopation, dotted rhythms
- Section-aware chord progressions (different patterns per section type)
- Diatonic 7th chords
- 4 skills populated (cinematic genre, voice-leading, piano, tension-resolution)
- v2 spec format with 11 sections (identity, emotion, melody, harmony, etc.)
- 3 v2 spec templates
- Composition Plan IR (CPIR) foundation: SongFormPlan, HarmonyPlan, MusicalPlan
- Plan generators: form planner, harmony planner
- MetricGoal type system for richer evaluation
- RecoverableDecision mechanism for traceable fallbacks
- 576 tests (unit, integration, scenario, constraint, golden, subagent evals)

**In progress (Phase alpha):**
- Completing CPIR as the required intermediary between specs and notes
- Golden MIDI test infrastructure
- Capability Matrix verification (`make matrix-check`)

**Next:**
- Negative space enforcement in generators
- More chord progression variety (secondary dominants, modulation)
- Multi-octave voice leading optimization
- MotifPlan, PhrasePlan, DrumPattern (Phase beta)
- Adversarial Critic with 30+ structured rules (Phase beta)

### Milestone 4: "My Style"
**User value:** YaO learns your preferences and produces music in your taste.

**Next:**
- Reference library matching (positive/negative references)
- Spec fragments and composability (extends/overrides in YAML)
- Style profile persistence
- Arrangement mode (reharmonize, regroove, reorchestrate)
- 12 genre Skills

### Milestone 5: "Production Ready"
**User value:** Use YaO output in a real project.

**Next:**
- DAW integration (Reaper MCP)
- LilyPond/MusicXML score export
- Mix engineer pipeline (EQ, compression, spatial)
- Multi-format export (stems, MusicXML, LilyPond, Strudel)

## Technical Roadmap

### Phase alpha (current): CPIR Foundation
1. SongFormPlan + HarmonyPlan as first-class intermediaries
2. Plan generators (form planner, harmony planner)
3. Note realizer refactoring (wrap legacy generators)
4. MetricGoal type system
5. RecoverableDecision mechanism
6. Golden MIDI test infrastructure
7. Capability Matrix validation

### Phase beta: Rich Plans
1. MotifPlan, PhrasePlan, DrumPattern, ArrangementPlan
2. Adversarial Critic with 30+ rules (Finding objects, not free text)
3. Multi-candidate Conductor
4. Markov chain generator
5. Constraint solver generator

### Phase gamma: Perception & Arrangement
1. Reference feature extraction (spectral, rhythmic, harmonic)
2. Similarity scoring between generated and reference works
3. Arrangement engine (reharmonization, style transfer)
4. Production manifest + mix chain

### Phase delta: Integration
1. DAW MCP integration
2. MusicXML / LilyPond / Strudel writers
3. Sketch dialogue state machine
4. Live mode

### Phase epsilon: Scale
1. AI bridge generator (external model integration via API)
2. Abstract AgentProtocol (backend-agnostic)
3. Session runtime with generation cache and feedback queue
