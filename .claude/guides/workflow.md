# Development Workflow

## Scaled by Change Size

### Tiny (1 file, <20 lines): bug fix, typo, small refactor
1. Read the file and its test
2. Make the change + update test
3. `make test-unit`

### Small (1-3 files, <100 lines): new helper, extend existing API
1. Read existing code in the area
2. Write failing test
3. Implement minimum to pass
4. `make all-checks`

### Medium (3-5 files, new feature): new generator, new render format
1. Write design intent in PR description
2. Read all affected files
3. Write tests (unit + integration)
4. Implement
5. `make all-checks`
6. Update docs if public API changed

### Large (5+ files, architecture): new layer component, protocol change
1. Write design doc in `docs/design/NNNN-topic.md`
2. Get human approval before implementing
3. Full test coverage (unit + integration + music_constraints)
4. `make all-checks`
5. Update CLAUDE.md/PROJECT.md if architectural rules change

## Decision Trees

### "New module or extend existing?"
1. Different layer? → new module
2. Existing module >300 lines? → consider splitting
3. New public API surface? → new module
4. Otherwise → extend existing

### "Add a new dependency?"
1. Can existing deps do it? → use existing
2. Pure Python, <5MB? → propose it
3. Requires native compilation? → make optional
4. GPL licensed? → do not use
5. Otherwise → ask human

### "Music theory decision to escalate?"
1. Clear rule in `.claude/skills/theory/`? → follow it
2. Well-known textbook rule? → apply it
3. Genre-dependent? → check skills/genres/
4. Matter of taste? → always ask human
