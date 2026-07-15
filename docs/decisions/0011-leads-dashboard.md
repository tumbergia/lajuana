# 0011 — Leads Dashboard

**Fecha:** 2026-07-13  
**Estado:** Superado por [0012 — Analítica e Insights](0012-analytics-insights.md)  
**Actualizado:** 2026-07-14

## Contexto

El Tablero Operativo tenía 4 subrutas (Resumen, Pendientes, Salidas, Sync) que
mostraban datos estáticos de fixtures y no reflejaban métricas reales del sistema.
Se necesitaba un panel de indicadores en vivo que reemplazara esa pantalla.

## Decisión (histórica)

Reemplazar el Tablero Operativo completo por un **Leads Dashboard** que:

1. Muestra hasta 5 indicadores en Inicio: **pins del usuario** (ordenados) +
   relleno aleatorio del pool elegible.
2. Pool elegible = `home_eligible=true` y no está en `excluded_lead_ids`.
3. Exporta a .xlsx (server-side con openpyxl).
4. Datos desde `GET /api/v1/analytics/leads` con caché en memoria de 5 min.
5. Preferencias en `UserDocument.leads_preferences`.

## Sucesión

A partir de ADR 0012 este diseño queda **superado**. Los endpoints `/analytics/leads*`
permanecen como adaptadores de compatibilidad hacia el motor v2. La selección
aleatoria ponderada se elimina. Ver [metric-audit.md](analytics/metric-audit.md)
para el destino de cada KPI legacy.
