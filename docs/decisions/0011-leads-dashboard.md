# 0011 — Leads Dashboard

**Fecha:** 2026-07-13

**Estado:** Implementado (actualizado 2026-07-14)

## Contexto

El Tablero Operativo tenía 4 subrutas (Resumen, Pendientes, Salidas, Sync) que
mostraban datos estáticos de fixtures y no reflejaban métricas reales del sistema.
Se necesitaba un panel de indicadores en vivo que reemplazara esa pantalla.

## Decisión

Reemplazar el Tablero Operativo completo por un **Leads Dashboard** que:

1. Muestra hasta 5 indicadores en Inicio: **pins del usuario** (ordenados) +
   relleno aleatorio del pool elegible. El relleno solo se regenera al cargar /
   pull-to-refresh.
2. Pool elegible = `home_eligible=true` y no está en `excluded_lead_ids` del usuario.
3. Permite expandir a la lista completa agrupada por categorías.
4. Exporta a .xlsx (server-side con openpyxl): individual por lead o todos
   juntos (una hoja por categoría).
5. Los datos se sirven desde `GET /api/v1/analytics/leads` con caché en memoria
   de 5 min.
6. Preferencias por usuario en
   `GET/PUT /api/v1/analytics/leads/preferences`
   (`pinned_lead_ids` máx. 5, `excluded_lead_ids`), persistidas en
   `UserDocument.leads_preferences`. Se pueden ocultar **cualquier** KPI
   (incluidos los de blacklist). La UI de configuración edita en lote y
   confirma con una barra sticky antes de persistir.
7. El relleno aleatorio es **ponderado** por `home_priority` (sesgo a ingresos,
   pagos y acciones de dinero).

## Cambios estructurales

### Backend

- `apps/api/app/schemas/analytics.py` — LeadItem (+ `home_eligible`), LeadCategory,
  AnalyticsResponse, LeadsPreferencesSchema
- `apps/api/app/services/analytics_service.py` — KPIs por categoría, queries
  paralelas, caché TTL 5 min, blacklist `HOME_INELIGIBLE_IDS`, métricas de
  bitácora equina (`EquineEventDocument`)
- `apps/api/app/api/endpoints/analytics.py` — GET /leads, GET/PUT preferences,
  GET /leads/export
- `UserDocument.leads_preferences` — pins y exclusiones por usuario

### Frontend

- `apps/mobile/lib/features/analytics/` — feature completo:
  - `remote/analytics_api_client.dart`
  - `presentation/controllers/leads_controller.dart` — selección home + prefs
  - `presentation/screens/leads_screen.dart` — Inicio
  - `presentation/screens/all_leads_screen.dart` — lista completa
  - `presentation/screens/configure_leads_screen.dart` — pins / exclusiones
  - widgets de card y sección

## Categorías de KPIs (7)

1. `accion` — Pendientes de accion
2. `reservas` — Embudo de reservas
3. `dinero` — Ingresos y pagos
4. `eq_operacion` — Equinos (operacion)
5. `eq_salud` — Equinos (salud) + bitácora (eventos 7d, cuidados vencidos/próximos,
   lesiones recientes, severidad alta)
6. `personas` — Participantes y origen
7. `catalogo` — Inventario y catalogo (mayoría con `home_eligible=false`)

## Blacklist de Inicio (`home_eligible=false`)

Totales / inventario / demografía lenta, p.ej. `eq_total`, `eq_mules`,
`eq_horses`, `eq_donkeys`, `par_total`, `par_avg_age`, `par_top_level`,
`ori_*`, `exp_total` / tipos de catálogo, `vol_total`, `pay_total`,
`op_usuarios`, `op_usuarios_total`. Siguen visibles en “Ver todos”.
