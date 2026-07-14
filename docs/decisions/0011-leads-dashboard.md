# 0011 — Leads Dashboard

**Fecha:** 2026-07-13

**Estado:** Implementado

## Contexto

El Tablero Operativo tenía 4 subrutas (Resumen, Pendientes, Salidas, Sync) que
mostraban datos estáticos de fixtures y no reflejaban métricas reales del sistema.
Se necesitaba un panel de indicadores en vivo que reemplazara esa pantalla.

## Decisión

Reemplazar el Tablero Operativo completo por un **Leads Dashboard** que:

1. Muestra 5 indicadores aleatorios del total al abrir la app (cambian con
   pull-to-refresh).
2. Permite expandir a la lista completa agrupada por categorías.
3. Exporta a .xlsx (server-side con openpyxl): individual por lead o todos
   juntos (una hoja por lead).
4. Los datos se sirven desde un nuevo endpoint REST
   `GET /api/v1/analytics/leads` con caché en memoria de 5 min.

## Cambios estructurales

### Backend

- `apps/api/app/schemas/analytics.py` — Schemas LeadItem, LeadCategory, AnalyticsResponse
- `apps/api/app/services/analytics_service.py` — Servicio con ~42 KPIs agrupados
  en 7 categorías, queries paralelas con `asyncio.gather`, caché TTL 5 min.
- `apps/api/app/api/endpoints/analytics.py` — Router con GET /leads y GET /leads/export
- Registrado en router.py, deps.py, di.py.
- Dependencia `openpyxl` agregada a pyproject.toml.

### Frontend

- `apps/mobile/lib/features/analytics/` — Nuevo feature completo:
  - `remote/analytics_api_client.dart` — HTTP client (sigue patrón existente)
  - `presentation/controllers/leads_controller.dart` — ChangeNotifier
  - `presentation/screens/leads_screen.dart` — Home con 5 cards aleatorias
  - `presentation/screens/all_leads_screen.dart` — Lista completa por categorías
  - `presentation/widgets/lead_card.dart` — Card individual
  - `presentation/widgets/lead_category_section.dart` — Sección expandible
- `apps/mobile/lib/features/dashboard/` **eliminado** (reemplazado por analytics)
- `test/dashboard/` **eliminado**

### Dependencias

- `apps/mobile/lib/app/dependency_injection.dart` — AnalyticsApiClient agregado
- `apps/mobile/lib/app/shell/authenticated_shell.dart` — analyticsApiClient inyectado
- `apps/mobile/lib/app/navigation/app_router.dart` — analyticsApiClient pasado al shell

## Categorías de KPIs

1. Volumen de reservas (~10 indicadores)
2. Ingresos (~4 indicadores)
3. Equinos (~10 indicadores)
4. Participantes (~6 indicadores)
5. Experiencias (~6 indicadores)
6. Pagos (~6 indicadores)
7. Operación (~5 indicadores)
