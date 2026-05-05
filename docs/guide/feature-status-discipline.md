# Feature Status Discipline

> How to maintain FEATURE_STATUS.md as the single source of truth.

## Purpose

FEATURE_STATUS.md is the **only place** that declares what YaO can and cannot do. README.md, CLAUDE.md, and PROJECT.md link to it instead of restating capabilities. This eliminates the drift that previously caused test count mismatches and feature overstatement.

## When to Update

Update FEATURE_STATUS.md **in the same PR** as any of these changes:

- Adding a new feature or module
- Removing or deprecating a feature
- Changing a feature's behavior or scope
- Adding or removing tests for a feature

## Status Criteria

| Status | Requirements |
|--------|-------------|
| ✅ **Stable** | Implementation exists, tests exist and pass, no known critical bugs |
| 🟢 **Working but limited** | Implementation exists, core path works, edge cases documented in Notes |
| 🟡 **Partial** | Some code exists but not all paths work; read Notes before depending |
| ⚪ **Designed, not started** | Specified in PROJECT.md but no implementation code |
| 🔴 **Identified gap** | Known need, acknowledged in roadmap, no code yet |

### Upgrading Status

- **🔴 → 🟡**: Implementation exists for at least one path + Notes describe what works
- **🟡 → 🟢**: Core functionality works + Notes describe limitations
- **🟢 → ✅**: Tests exist and pass + no known critical limitations
- **⚪ → 🔴**: Decision made that this feature is needed (roadmap entry)

### Downgrading Status

- Any downgrade (✅ → lower) requires explicit justification in the PR description
- Document the reason in the Notes column

## Verification Tool

```bash
make feature-status
```

This runs `tools/feature_status_check.py`, which:

1. Parses all tables in FEATURE_STATUS.md
2. For each ✅ entry with a mapping in `tools/feature_status_mapping.yaml`, verifies source files and test files exist
3. Reports warnings (exit 0) — it does not block development

### Adding Mappings

When you add a new ✅ entry, add a corresponding key in `tools/feature_status_mapping.yaml`:

```yaml
"My New Feature":
  src:
    - src/yao/module/my_feature.py
  tests:
    - tests/unit/test_my_feature.py
```

## What NOT to Do

- **Do not add aspirational entries as ✅** — if it doesn't work yet, it's not ✅
- **Do not update FEATURE_STATUS.md without updating the code** (or vice versa)
- **Do not duplicate capability claims in README.md or CLAUDE.md** — link to FEATURE_STATUS.md instead
- **Do not change a feature's status based on plans** — status reflects current reality

## PR Checklist

Every PR that touches `src/yao/` should include:

- [ ] `FEATURE_STATUS.md` updated if feature status changed
- [ ] `make feature-status` passes
- [ ] No numeric capability claims added to README.md or CLAUDE.md
