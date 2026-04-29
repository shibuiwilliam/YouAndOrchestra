# /arrange — Arrange an existing composition

## Purpose
Take an existing composition and transform it through arrangement operations: reharmonization, regrooving, reorchestration, or style transfer.

## Arguments
- `$ARGUMENTS` — Project name

## Protocol

1. **Load source material**: Read the existing composition from the project
2. **Identify arrangement goals**: Ask the user what transformations they want:
   - Reharmonize (change chord progressions while keeping melody)
   - Regroove (change rhythmic feel)
   - Reorchestrate (change instrumentation)
   - Style transfer (transform from one genre to another)
3. **Read arrangement.yaml** if it exists, or create one through dialogue
4. **Apply transformations**: Use the arrangement engine to transform the composition
5. **Compare with original**: Generate a diff showing what changed
6. **Present for approval**: Show the changes and ask the user to approve

## Status
Phase 2 feature — arrangement engine not yet fully implemented.
Currently supports basic re-generation with modified specs.

## Uses
- Subagents: Orchestrator, Adversarial Critic
- Skills: theory/reharmonization, genre skills
