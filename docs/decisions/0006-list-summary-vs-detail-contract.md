# ADR-0006: Contrato list-summary vs detail para endpoints mobile

**Fecha:** 2026-05-26  
**Estado:** Aceptado  
**Contexto:** Corrección del anti-pattern N+1 en reservas que obligaba al frontend a hidratar el listado con llamadas de detalle por item.

## Problema

El endpoint `GET /api/v1/reservations` devolvía un `ReservationListItemSchema` demasiado pobre, insuficiente para pintar las cards del listado móvil. El frontend compensaba haciendo `GET /api/v1/reservations/{id}` por cada item del listado, generando un N+1 innecesario y lentitud.

## Decisión

Todo endpoint de listado que alimente una vista de lista/tabla en mobile debe devolver un **summary contract** suficiente para:

- pintar la fila o card sin llamadas adicionales
- ordenar localmente
- filtrar por estado
- mostrar badges y contadores esenciales
- navegar al detalle

El endpoint de detalle se reserva para la vista de detalle (al hacer tap en un item).

## Contrato

### Regla 1: List endpoint → summary suficiente

```
GET /entities → 200 list[EntitySummarySchema]
```

`EntitySummarySchema` debe incluir todos los campos que la vista de lista necesita para renderizar sin llamadas complementarias.

Para reservas, los campos mínimos son:

```
id, code, status, participant_count, payment_status,
holder_name, holder_phone,
experience_id, experience_name,
schedule_id, requested_date, scheduled_date, start_time,
expected_participants_count, participants_completed_count,
participant_form_status, channel,
version, created_at, updated_at
```

### Regla 2: Detail endpoint → contrato completo

```
GET /entities/{id} → 200 EntityDetailSchema
```

Se consume exclusivamente al navegar al detalle.

### Regla 3: Frontend zero hydration

- `list*()` consume **solo** el list endpoint
- `getById()` consume **solo** el detail endpoint
- No se hacen llamadas de detalle para completar el listado
- Cache local separada: summaries en tabla `*_list_cache`, detalles en `*_detail_cache`

### Regla 4: Denormalización en backend

Cuando el summary requiera datos de colecciones relacionadas (ej: `experience_name` en reservas), el backend los resuelve en batch.

Patrón:

```
1. Fetch list documents
2. Collect unique related IDs (experience_ids, schedule_ids, etc.)
3. Batch-fetch related documents
4. Build lookup dicts
5. Map enriched response
```

Esto mantiene el endpoint en ~3 queries totales independientemente del tamaño de la lista.

## Anti-pattern explícito: prohibido

No hidratar listas con el endpoint de detalle.  
Ningún frontend ni repositorio debe hacer:

```dart
// MAL ❌ — N+1 para completar listado
final ids = await api.list();  // 1 call
for (final id in ids) {
  final detail = await api.getById(id);  // N calls
}
```

```dart
// BIEN ✅ — summary suficiente desde list
final items = await api.list();  // 1 call
```

## Aplicación a otros módulos

Este mismo patrón debe seguirse para:

- Equinos: `GET /equines` → `list[EquineResponseSchema]` (ya es suficiente)
- Participantes: endpoint de listado (cuando exista)
- Proveedores: endpoint de listado (cuando exista)
- Asignaciones: endpoint de listado (cuando exista)

Si en el futuro un módulo requiere más datos en la card de los que su list schema entrega, se debe enriquecer el **list schema**, no hidratar desde el detail.

## Archivos afectados

### Backend
- `apps/api/app/schemas/reservation.py` — `ReservationListItemSchema`
- `apps/api/app/services/mappers.py` — `reservation_to_list_item()`
- `apps/api/app/api/endpoints/reservations.py` — batch resolution

### Frontend
- `apps/mobile/lib/features/reservations/infrastructure/remote/reservation_dtos.dart`
- `apps/mobile/lib/features/reservations/infrastructure/mappers/reservation_mapper.dart`
- `apps/mobile/lib/features/reservations/infrastructure/repositories/reservations_repository_impl.dart`

## Referencias

- Contrato observado: `docs/mobile/reservations-api-contract-observed.md`
- Arquitectura API: `docs/architecture/api.md`
- Arquitectura mobile: `docs/architecture/mobile.md`
