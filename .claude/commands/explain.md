# /explain — Explain a specific generation decision

## Purpose
Look up the provenance for a specific musical element and explain why it was generated that way.

## Arguments
- `$ARGUMENTS` — What to explain (e.g., "chord at bar 8", "melody in chorus", "bass pattern")

## Protocol

1. **Parse the query**: Identify which musical element the user is asking about
2. **Load provenance.json**: Find relevant provenance records
3. **Trace the decision chain**: Follow the provenance from the final note back to:
   - Which generator produced it
   - What parameters influenced it
   - What trajectory values were active at that point
   - What spec constraints applied
4. **Explain in musical terms**: Translate the technical rationale into musical language
5. **Show alternatives**: If applicable, describe what other options were considered

## Uses
- Subagent: Producer (Provenance reference)
