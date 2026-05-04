# Design: Hook IR + Phrase-Level Dynamics (Phase γ.3)

## Problem
Compositions lack memorable centerpieces. Even surprising music feels formless without hooks and dynamics shaping.

## Solution
- Hook IR: frozen dataclass with deployment strategy (rare/frequent/withhold_then_release/ascending_repetition), appearances, distinctive_strength
- HookPlan: embedded in MusicalPlan, references MotifSeed by id
- DynamicsShape: per-section velocity curve (crescendo/decrescendo/arch/hairpin/steady)
- 4 critique rules: hook_overuse, hook_underuse, hook_misplacement, flat_phrase_dynamics
