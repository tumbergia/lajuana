# ADR-0015: Optimización de tokens del prompt del planner (WhatsApp)

**Fecha:** 2026-07-16  
**Estado:** ✅ Aceptado  
**Complementa:** [0005 — Pipeline chatbot v2](0005-chatbot-pipeline.md)

## Contexto

Cada mensaje de WhatsApp que cae al planner LLM enviaba un system prompt
de ~24k caracteres (~6.500–7.800 `prompt_tokens` en telemetría real). El
coste no tenía sentido: gran parte del texto era catálogo de tools
hardcodeado y verboso, reglas duplicadas y ejemplos redundantes con el
schema estructurado.

Ya existía un catálogo compacto en
`apps/api/app/ai/assistant/tool_catalog.py` (`render_tools_for_prompt`)
que no estaba cableado al prompt de producción.

## Decisión

1. **Catálogo compacto cableado**: `PLANNER_SYSTEM_PROMPT` recibe
   `{tools_section}` generado por `render_tools_for_prompt(channel)`.
2. **Reglas deduplicadas**: una sola versión de cada regla crítica
   (catálogo, precios, flujo `check_availability_and_quote`, pago,
   alcohol, seguridad admin, desambiguación de "link").
3. **Ejemplos mínimos**: se eliminan bloques "Formato de argumentos";
   quedan solo ejemplos de flujo que desambiguan.
4. **Historial WhatsApp**: 4 turnos (antes 8 fijos) + truncado a 400
   chars por mensaje. Admin/mobile/test siguen en 8.
5. **Composer**: recorte ligero de estilo, sin tocar reglas de idioma.

Validación con `apps/api/scripts/prompt_benchmark.py` (golden set de 27
queries, planner directo sin intent router):

| Métrica | Baseline | After |
|---------|----------|-------|
| `prompt_tokens` avg | 6469.8 | 2508.6 |
| Reducción | — | **61.2%** |
| Soft accuracy | 100% | 100% |
| Critical soft | 13/13 | 13/13 |

Criterios de aceptación cumplidos: avg ≤ 3800, reducción ≥ 45%, soft
accuracy ≥ baseline y ≥ 90%, cero regresiones en casos críticos.

## Consecuencias

- Menor coste por mensaje WhatsApp cuando el intent router no matchea.
- El catálogo de tools vive en un solo lugar (`tool_catalog.py`).
- Guard de regresión: `tests/test_planner_prompt_size.py` falla si el
  prompt renderizado supera ~12k chars.
- El historial más corto puede perder contexto antiguo en WhatsApp; 4
  turnos + slots de sesión cubren el flujo de reserva típico.

## Cómo re-benchmarkear

```bash
cd apps/api
.venv/Scripts/python.exe scripts/prompt_benchmark.py --label baseline
# ... aplicar cambios ...
.venv/Scripts/python.exe scripts/prompt_benchmark.py --label after \
  --compare scripts/benchmark_results/baseline.json
```

Los JSON de resultado van a `apps/api/scripts/benchmark_results/`
(gitignored).
