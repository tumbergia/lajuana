# How to add an API endpoint

## Paso a paso

### 1. Schema (si aplica)

Crear schema Pydantic en `apps/api/app/schemas/`:

```python
# apps/api/app/schemas/mi_entidad.py
from pydantic import BaseModel

class MiEntidadCreateSchema(BaseModel):
    name: str = Field(min_length=3)
    description: str | None = None

class MiEntidadResponseSchema(AuditMetadataSchema):
    id: str
    name: str
```

Convención:
- Create: todos los campos required
- Update: todos optional (`| None = None`)
- Response: extiende `AuditMetadataSchema`

### 2. Endpoint

Agregar a router existente o crear nuevo en `apps/api/app/api/endpoints/`:

```python
# apps/api/app/api/endpoints/mi_entidad.py
from fastapi import APIRouter, Depends, status
from app.api.deps import require_permissions, get_mi_entidad_service
from app.common.enums import Permission
from app.schemas.mi_entidad import MiEntidadCreateSchema, MiEntidadResponseSchema

router = APIRouter(prefix="/mi-entidad", tags=["Mi Entidad"])

@router.post(
    "",
    response_model=MiEntidadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear mi entidad",
)
async def create_mi_entidad(
    payload: MiEntidadCreateSchema,
    _ = Depends(require_permissions(Permission.MI_ENTIDAD_CREATE)),
    service = Depends(get_mi_entidad_service),
) -> MiEntidadResponseSchema:
    doc = await service.create(payload)
    return mi_entidad_to_response(doc)
```

### 3. Servicio (si no existe)

Crear o usar servicio en `apps/api/app/services/`:

```python
class MiEntidadService(BaseService[MiEntidadDoc, MiEntidadCreate, MiEntidadUpdate]):
    document_class = MiEntidadDocument
    not_found_code = ErrorCode.MI_ENTIDAD_NOT_FOUND
```

### 4. Registrar router

En `apps/api/app/api/router.py`:

```python
from app.api.endpoints.mi_entidad import router as mi_entidad_router
api_router.include_router(mi_entidad_router)
```

### 5. Registrar en DI

En `apps/api/app/core/di.py`:

```python
self._services["mi_entidad_service"] = MiEntidadService()
```

En `apps/api/app/api/deps.py`:

```python
def get_mi_entidad_service() -> MiEntidadService:
    return Container.get_instance().mi_entidad_service
```

### 6. Tests

```python
# apps/api/tests/test_mi_entidad_service.py
@pytest.mark.asyncio
async def test_create_mi_entidad():
    ...
```

### 7. Documentación

- Si es un endpoint nuevo relevante, agregar a `docs/api/ENDPOINTS.md`
- Si hay nuevos errores, agregar a `docs/api/ERRORS.md`

## Checklist

- [ ] Schema Pydantic creado
- [ ] Endpoint con response_model, status_code, summary
- [ ] Auth con `require_permissions()`
- [ ] Router registrado en `api/router.py`
- [ ] Servicio registrado en DI
- [ ] Tests pasan
- [ ] Si es GET list: soporta `skip`/`limit` y `X-Total-Count`
- [ ] Si es DELETE: soft delete (set `deleted_at`)
