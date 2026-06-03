# ADR-0006: Contrato list-summary vs detail

**Fecha:** 2026-05-25  
**Estado:** ✅ Aceptado  

## Contexto

Endpoint GET /reservations devolvía datos completos. En lista de 50+ items, payload pesado generaba N+1 queries para participantes y comprobantes.

## Decisión

Separación contratos:
- `ReservationListItemSchema`: resumen liviano (sin participantes, sin comprobantes)
- `ReservationDetailSchema`: detalle completo (con participantes, payment proofs, timeline)
- `GET /reservations` → lista de `ListItem`
- `GET /reservations/{id}` → `Detail`

## Consecuencias

- Lista de 50 reservas: ~3 queries vs ~150 queries antes
- Mobile cachea list y detail por separado
- Detail se pide on-demand al abrir una reserva
- `batch_assignments_to_response()` para board elimina N+1 en asignaciones
