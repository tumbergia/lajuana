# Principios arquitectónicos (cross-cutting)

Reglas que aplican a backend y frontend por igual.

## 1. Reserva es la entidad central

Toda funcionalidad existe para gestionar reservas. Equinos, sillas,
experiencias, participantes, pagos — son medios para ese fin.

## 2. Backend es fuente de verdad

Validaciones críticas (disponibilidad, capacidad, estados) se resuelven
en backend. Frontend muestra estado, no decide.

## 3. Mobile-first, offline-first

La app móvil es el punto de operación principal. Debe funcionar con
conectividad intermitente. SQLite local cachea datos; sync incremental
sincroniza cambios.

## 4. No mezclar capas

```
UI reusable (packages/mobile_ui/) 
  → NO debe importar lógica de negocio
  → NO debe conocer modelos de dominio

Lógica de negocio (packages/mobile_domain/)
  → Modelos puros, sin Flutter, sin IO
  → Interfaces de repositorio, no implementaciones

Infraestructura (apps/mobile/lib/features/*/infrastructure/)
  → API clients, SQLite, mappers
```

## 5. Un concepto, un lugar

| Concepto | Dónde vive |
|----------|-----------|
| Widget reusable | `packages/mobile_ui/lib/src/widgets/` |
| Modelo de dominio | `packages/mobile_domain/lib/src/` |
| DTO (API) | `*/*/infrastructure/remote/*_dtos.dart` |
| Endpoint | `apps/api/app/api/endpoints/*.py` |
| Servicio | `apps/api/app/services/*.py` |
| Documento DB | `apps/api/app/documents/*.py` |

## 6. Sin silenciar errores

Cero `except: pass`. Todo error se loggea con `logger.exception()`.
Política: fail-fast para validaciones, fail-open para operaciones no críticas.

## 7. Código de prueba fuera de producción

- Dev screens en `dev/playground/` (release-guarded con `kReleaseMode`)
- Tests en directorio `test/` espejando estructura de `lib/`
- Sin mocks, fakes, ni playground en `lib/`

## 8. API como contrato

- Backend expone OpenAPI spec en `/openapi.json`
- Modelos Dart se generan desde OpenAPI (`tools/openapi_gen/`)
- No duplicar definiciones de datos entre Flutter y Python
- Errores negociados: frontend depende de `ErrorCode` strings, no de mensajes

## 9. Cambio estructural = actualizar docs

Cada PR que toca estructura (nuevo archivo, capa, ruta, modelo) debe
actualizar al menos uno de: `docs/architecture/*`, `docs/conventions/*`,
`docs/decisions/*`.
