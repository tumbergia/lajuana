# ADR-0005: Pipeline chatbot v2

**Fecha:** 2026-05-15  
**Estado:** ✅ Aceptado  

## Contexto

El chatbot original usaba prompts monolíticos. Difícil de testear, permisos frágiles, tools acopladas al prompt.

## Decisión

Pipeline en 4 etapas:

1. **Planner** (Gemini) → genera `AssistantPlan` estructurado (acción, tool, args, confianza)
2. **Policy Engine** → valúa permisos por canal, autocorrige typos, bloquea tools críticas
3. **Tool Execution** → registry MCP ejecuta la tool
4. **Composer** → tool output → respuesta natural

## Consecuencias

- +55 tools MCP registradas y permisos granulares por canal (client/guide/admin)
- Tools categorizadas: READ, LIMITED_WRITE, WRITE, CRITICAL
- Tools destructivas requieren confirmación explícita
- Policy engine con autocorrección de typos (difflib, cutoff 0.75)
- ~1700 líneas de documentación de endpoints generada
