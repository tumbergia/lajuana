# Decisiones arquitectónicas (ADRs)

Registro cronológico de decisiones significativas.

## Índice

| # | Título | Estado | Fecha |
|---|--------|--------|-------|
| 0001 | [Monorepo](0001-monorepo.md) | ✅ Aceptado | 2026-04-22 |
| 0002 | [Design system propio](0002-design-system.md) | ✅ Aceptado | 2026-04-22 |
| 0003 | [Navegación por voz](0003-voice.md) | 🟡 Prototipo | 2026-04-22 |
| 0004 | [Extracción mobile UI a packages](0004-mobile-ui-extract.md) | ⏳ Postergado | 2026-06-02 |
| 0005 | [Pipeline chatbot v2](0005-chatbot-pipeline.md) | ✅ Aceptado | 2026-05-15 |
| 0006 | [Contrato list-summary vs detail](0006-list-detail-contract.md) | ✅ Aceptado | 2026-05-25 |
| 0007 | [Datos holder obligatorios](0007-holder-data.md) | ✅ Aceptado | 2026-06-01 |
| 0008 | [Protocolo offline-first sync](0008-offline-sync.md) | ✅ Aceptado | 2026-06-01 |
| 0009 | [Separación auth/network](0009-auth-network.md) | ✅ Aceptado | 2026-04-23 |
| 0010 | [Política de lenguaje del bot](0010-bot-language-policy.md) | ✅ Aceptado | 2026-06 |
| 0011 | [Leads Dashboard](0011-leads-dashboard.md) | ♻️ Superado | 2026-07-13 |
| 0012 | [Analítica e Insights](0012-analytics-insights.md) | ✅ Aceptado | 2026-07-14 |

Auditoría de métricas: [analytics/metric-audit.md](analytics/metric-audit.md)

## Template para nuevos ADRs

```markdown
# ADR-XXXX: Título descriptivo

**Fecha:** YYYY-MM-DD
**Estado:** [Aceptado | Postergado | Rechazado]

## Contexto
¿Qué problema resolvemos? ¿Qué opciones consideramos?

## Decisión
¿Qué elegimos y por qué?

## Consecuencias
Qué cambia, qué se rompe, qué mejora.

## Alternativas consideradas
- Opción A: pro/contra
- Opción B: pro/contra
```
