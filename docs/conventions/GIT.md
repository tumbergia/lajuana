# Git Conventions

## Branches

| Branch | Propósito |
|--------|-----------|
| `main` | Stable, deployable |
| `develop` | Integration branch |
| `feat/*` | New features |
| `fix/*` | Bug fixes |
| `chore/*` | Maintenance |
| `docs/*` | Documentation |

## Commits

Prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`

Subject ≤ 50 chars. Body only when "why" isn't obvious.

## PR flow

1. Branch from `develop`
2. Implement + test
3. PR to `develop` with checklist
4. CI must pass (quality gate)
5. Squash merge

## PR checklist

From `.github/PULL_REQUEST_TEMPLATE.md`:

- [ ] AGENTS.md rules followed
- [ ] No `except: pass` or silent error swallowing
- [ ] All errors logged with `logger.exception()`
- [ ] Tests added or updated
- [ ] No generated files/mocks/playground in production
- [ ] If structural changes: docs/ updated
- [ ] `flutter analyze` passes with 0 errors
- [ ] `pytest` passes for modified backend code

## CI

Two workflows:
- `quality.yml` — push/PR: ruff lint + format + pytest (backend); dart format + analyze + test (mobile)
- `openapi-gen-check.yml` — PR touching schemas: verify Dart models match OpenAPI spec
