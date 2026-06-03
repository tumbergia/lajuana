# Backend Conventions (Python / FastAPI)

## Config

| Setting | Value |
|---------|-------|
| Python | 3.11+ |
| Linter | ruff (select: E, F, I, UP, B) |
| Line length | 100 |
| Quotes | double |
| Formatter | `ruff format` |
| Type checker | mypy (exclude: tests/, scripts/, seed_, migrations/) |
| Test runner | pytest (asyncio_mode = auto) |
| Integration marker | `@pytest.mark.integration` |

## Naming

| Element | Style | Example |
|---------|-------|---------|
| Files/modules | `snake_case` | `experience_service.py` |
| Classes | `PascalCase` | `ExperienceService` |
| Functions | `snake_case` | `get()`, `_validate_pricing()` |
| Constants | `UPPER_SNAKE` | `ERROR_CODE_USER_NOT_FOUND` |
| Type vars | `NameT` | `DocT`, `CreateSchemaT` |

## Imports order

1. `from __future__ import annotations`
2. Standard library
3. Third-party (fastapi, beanie, pydantic, jwt)
4. First-party (`app.*`)

## Service patterns

**BaseService (preferred for CRUD):**
```python
class SaddleService(BaseService[SaddleDoc, SaddleCreate, SaddleUpdate]):
    document_class = SaddleDocument
    not_found_code = ErrorCode.SADDLE_NOT_FOUND
```

Methods: `get()`, `list()`, `count()`, `create()`, `update()`, `soft_delete()`, `restore()`.

**Hand-rolled (domain-heavy):**
`ReservationService`, `ExperienceService`, `PaymentProofService` — complex logic, no base class.

## Schema patterns (Pydantic)

| Tipo | Sufijo | Regla |
|------|--------|-------|
| Create | `*CreateSchema` | All required |
| Update | `*UpdateSchema` | All optional (`\| None = None`) |
| Response | `*ResponseSchema` | Extends AuditMetadataSchema |
| Nested | `*NestedSchema` | For sub-objects |

## Error handling

```python
raise ApiError(
    status_code=404,
    code=ErrorCode.RESERVATION_NOT_FOUND,
    message="Reserva no encontrada.",
    details={"reservation_id": rid},
)
```

- Error codes: `{domain}.{specific_error}` format in `common/labels.py`
- Never `except: pass` → use `logger.exception()`
- `logger.warning()` for recoverable issues
- `logger.info()` for lifecycle events

## DI pattern

Manual singleton container (`app/core/di.py`). `Container.init()` in lifespan.
Services injected via `Depends(get_xxx_service)` in endpoints.

## Test patterns

- One `test_*.py` per service
- mongomock_client fixture for unit tests
- `@pytest.mark.integration` for real MongoDB tests
- monkeypatch for service mocking
- `APP_SKIP_DB_INIT=true` in conftest
- No integration tests in CI

## Document patterns (Beanie)

- Base: `AuditDocument` with `version`, `created_at`, `updated_at`, `deleted_at`
- Collection: `class Settings: name = Collections.ENTITY`
- Indexes: `IndexModel` in `Settings.indexes`
- Soft delete: `deleted_at: datetime | None = None`
