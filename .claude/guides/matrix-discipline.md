# Capability Matrix Discipline

The Capability Matrix in [PROJECT.md §4](../../PROJECT.md#4-capability-matrix-single-source-of-truth) is the **single source of truth** for what YaO can and cannot do. This guide defines the rules for maintaining it.

---

## Status Definitions

| Status | Meaning | Requirements |
|---|---|---|
| ✅ Implemented | Working with tests; safe to depend on | Source files exist, tests pass, functionality is complete for stated scope |
| 🟢 Working but limited | Core works; check edge cases | Source files exist, tests pass, but known limitations exist (documented in Notes) |
| 🟡 Partial | Some paths work | Some code exists but incomplete; **must include `limitation:` in Notes column** |
| ⚪ Designed, not started | Design exists in PROJECT.md but no code | No source files; do not import or depend on |
| 🔴 Identified gap | Known need, no design detail | Do not plan around; treat as future target |

---

## Rules

### 1. Implementation drives status, not aspiration

A feature's status reflects what the code does **today**, verified by `make matrix-check`. You may never set a status higher than what the code supports.

### 2. Every PR that changes a feature updates the matrix

If you add, modify, or remove functionality, update the corresponding matrix row in the same PR. The `make matrix-check` target enforces this for ✅ entries.

### 3. Downgrades require escalation

Changing a status from ✅ to anything else (regression) must be flagged in the PR description and approved by the maintainer. This prevents silent capability loss.

### 4. ✅ entries require a mapping

Every ✅ feature must have a corresponding entry in `tools/capability_matrix_mapping.yaml` listing its source files and test files. The `make matrix-check` target verifies these files exist.

### 5. Notes column is mandatory for 🟢 and 🟡

These statuses indicate known limitations. The Notes column must describe what works and what doesn't, using the prefix `limitation:` for clarity.

### 6. No hardcoded counts in other documents

README.md, CLAUDE.md, and other documents must not include absolute counts (e.g., "226 tests", "46 instruments") that can drift. Instead, link to the Capability Matrix.

---

## Verification

```bash
# Check that all ✅ entries have matching source and test files
make matrix-check

# Full check including matrix
make all-checks    # lint + arch-lint + matrix-check + test
```

The `tools/capability_matrix_check.py` script:
1. Parses the matrix table from PROJECT.md §4
2. Loads file path mappings from `tools/capability_matrix_mapping.yaml`
3. For each ✅ entry with a mapping, verifies source and test files exist
4. Exits with code 1 if any inconsistency is found

---

## Adding a new feature to the matrix

1. Add a row to the table in PROJECT.md §4 with the appropriate status
2. If the status is ✅, add a mapping entry in `tools/capability_matrix_mapping.yaml`
3. Run `make matrix-check` to verify
4. Include the matrix update in your PR

---

## Mapping file format

`tools/capability_matrix_mapping.yaml` maps feature names (matching the Feature column exactly) to file paths:

```yaml
"feature name as in matrix":
  src:
    - path/to/source.py
  tests:
    - tests/unit/test_file.py
```

Both `src` and `tests` are optional. If a feature has no natural test file (e.g., agent definitions), omit the `tests` key.
