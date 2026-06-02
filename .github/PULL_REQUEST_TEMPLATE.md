# Pull Request

## Description

<!-- Briefly describe the change, motivation, and affected area. -->

## Checklist

- [ ] **AGENTS.md rules** followed (no business logic in widgets, no silent errors, no code outside defined layers)
- [ ] **No `except: pass`** or silent error swallowing — all errors are logged with `logger.exception()`
- [ ] **Tests** added or updated for the change
- [ ] **No generated files, mocks, or playground code** mixed with production code
- [ ] **If structural changes**: at least one of `docs/architecture/*`, `docs/conventions/*`, `docs/decisions/*` updated
- [ ] **`flutter analyze`** passes with 0 errors (pre-existing warnings/infos are OK)
- [ ] **`pytest`** passes for modified backend code

## Verification

<!-- How was this tested? Include commands run. -->
