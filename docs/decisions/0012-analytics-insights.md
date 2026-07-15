# ADR-0012: Analítica e Insights (sucesor de Leads)

**Fecha:** 2026-07-14  
**Estado:** Aceptado (migración incremental)  
**Sucede a:** [0011 — Leads Dashboard](0011-leads-dashboard.md)

## Contexto

El dashboard "Leads" (ADR 0011) entregaba KPIs útiles pero con problemas de producto:

1. Selección aleatoria ponderada en Inicio (no determinista, confusa).
2. Etiquetas financieras incorrectas ("facturado" sobre montos cotizados).
3. Conversión comercial no defendible.
4. Valores solo como `str`; sin series tipadas ni periodo.
5. Sin offline-first; sin gráficas; export XLSX por categoría técnica.
6. País como texto libre sin ISO.

Se requiere un sistema de **Analítica e Insights** orientado a administradores y guías de La Juana, no a desarrolladores.

## Decisión

1. **Renombre conceptual:** "Leads" → "Analítica" / "Insights". Rutas legacy `/analytics/leads*` se mantienen y delegan al motor v2.
2. **Eliminar aleatoriedad** en Inicio. El usuario elige hasta **4 módulos** predefinidos (nunca queries arbitrarias).
3. **Contratos v2 discriminados** por visualización (`kpi`, `sparkline`, `line`, `bar`, `donut`, `progress`, `ranking`, `action_list`) con `primary_value` numérico, series tipadas, comparación con umbrales, `insight_text` determinista (sin IA).
4. **Tareas pendientes** (`action_center`) aparece automáticamente con pendientes críticos y no se puede ocultar mientras tenga contenido.
5. **Offline-first:** snapshot SQLite por usuario/módulos/rango/comparación/schema; UI abre local y refresca en segundo plano.
6. **Export XLSX** server-side con 4 hojas visibles de negocio (`Resumen`, `Indicadores`, `Tendencias`, `Desgloses`); metadata técnica oculta; logo opcional.
7. **Países:** normalización backend a ISO 3166-1 alpha-2 + backfill; Flutter no normaliza.
8. **Semántica financiera:**
   - Valor cotizado = suma de cotizaciones.
   - Valor confirmado (UI: "Ingresos comprometidos") = `quoted_total_amount` de confirmadas/completadas.
   - Ingreso cobrado = **bloqueado** (no hay montos en comprobantes).
   - Conversión comercial = **bloqueada**; se muestra distribución de estados.
9. **Ocupación** = participantes confirmados de próximas salidas vs cupo de la experiencia (`standard_max_participants` / `base_capacity`), no "capacidad del schedule" (inexistente).
10. **UI de negocio:** ningún ID técnico, enum, schema o timestamp ISO visible. Vocabulario de La Juana.
11. **Tokens:** `AnalyticsVisualTokens` + `fl_chart` / `country_flags`; sin colores hardcodeados en widgets.

## Consecuencias

- Un solo motor de cálculo (`analytics_query_service`); legacy adapta.
- Preferencias v2 en `UserDocument.analytics_preferences` con migración lazy desde `pinned_lead_ids`.
- Catálogo filtrado por permisos del rol.
- Flutter reutiliza `mobile_ui`; no estética paralela.
- Deuda documentada: ingreso cobrado y conversión comercial hasta que existan datos.

## Alternativas consideradas

- Mantener leads + capa cosmética de gráficas: rechazado (semántica rota).
- Redis para caché: rechazado (no existe en el repo; dict TTL por query key es suficiente).
- Embudo de conversión improvisado: rechazado (engañaría al negocio).
- Capacidad inventada de schedule: rechazado; ocupación redefinida vs experiencia.

## Referencias

- Auditoría de métricas: [analytics/metric-audit.md](analytics/metric-audit.md)
- Endpoints v2: `/api/v1/analytics/dashboard*`
- Legacy: `/api/v1/analytics/leads*`
