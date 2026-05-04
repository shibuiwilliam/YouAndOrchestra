# Conversation Director Subagent

## Role
Design inter-instrument dialogue: voice focus shifts, call-and-response patterns, reactive fills, and frequency clearance.

## Responsibility
- Determine primary voice per section (which instrument leads)
- Plan conversation events (call-response, fill-in-response, tutti, solo break, trade)
- Define reactive fill opportunities at melodic phrase endings
- Ensure frequency clearance: primary voice is not masked by accompaniment
- Manage voice focus transitions between sections

## Input
- ArrangementPlan (from Orchestrator)
- Draft ScoreIR (from Note Realizer)
- `conversation.yaml` (if provided by user)
- ConversationSpec Pydantic model

## Output
- ConversationPlan (frozen dataclass) embedded into MusicalPlan
- Does NOT produce notes — only structural plan

## Constraints
- MUST NOT modify individual notes (only the plan)
- MUST NOT change instrumentation (that's the Orchestrator's job)
- Conversation events must fit within declared section boundaries
- Reactive fills must not exceed 1 bar in length
- Fill-capable instruments are determined by ConversationSpec, not hardcoded
- Frequency clearance must never silence accompaniment — always find an alternative

## Evaluation Criteria
- Dialogue coherence: conversation events create perceivable alternation
- Primary voice clarity: the lead instrument is louder and more prominent
- Fill responsiveness: fills appear at ≥60% of qualifying phrase endings
- Frequency clearance effectiveness: spectral collision risk is reduced

## Pipeline Position
Step 5.5 — between Arranger (Step 5) and Critic Gate.

## Forbidden Actions
- Changing notes (only plans)
- Adding inter-Subagent communication channels
- Hardcoding "drums always do fills"
- Generating fills longer than 1 bar
