# ADR-0016: Base de conocimiento corporativa (RAG ligero)

**Fecha:** 2026-07-16  
**Estado:** ✅ Aceptado  
**Complementa:** [0005 — Pipeline chatbot v2](0005-chatbot-pipeline.md), [0015 — Tokens prompt](0015-prompt-token-optimization.md)

## Contexto

El bot de WhatsApp no tenía fuente de verdad para historia, fundadores,
cultura cafetera, UNESCO/PCC ni sostenibilidad. Esas preguntas caían al
LLM y podían alucinar (años, contactos, políticas).

Ya existía `get_public_business_rules` para ubicación/edades/anticipación
desde Mongo. Mezclar narrativa estática con config live en el mismo canal
era riesgoso.

No queríamos Chroma/LangChain ni inflar tokens en cada turno de reserva
(ADR-0015).

## Decisión

1. **Fuente estática versionada:** `apps/api/app/ai/knowledge/la_juana_empresa.md`
   (ES) y `la_juana_empresa.{lang}.md` para en/fr/de/it/ru/zh/ja, en primera
   persona (“somos / we”). Disclaimer de no inventar datos operativos.
2. **Índice local por idioma:** chunks por heading + embeddings Gemini;
   JSON en `knowledge/.index/la_juana_empresa.{lang}.index.json` (gitignored).
3. **Tool MCP** `search_company_knowledge(query)` → top-k=3 sobre el índice del
   **idioma de sesión**, response literal + CTA en ese idioma.
4. **Intent router:** keywords de historia/fundadores/cultura/UNESCO/Neira
   → fuerza la tool. Ubicación/edades siguen en `get_public_business_rules`.
5. **Planner:** misma desambiguación; **no** inyectar RAG en turnos de
   reserva/cotización.
6. **Separación de verdades:** si MD y Mongo chocan en ubicación, gana Mongo.

Reindex: `make knowledge-index` o
`python -m scripts.index_company_knowledge --force`.

## Consecuencias

- Preguntas “quiénes fundaron / qué es La Juana / UNESCO” responden desde MD.
- Flujo de reserva (`check_availability_and_quote`, catálogo) intacto.
- Coste de embeddings solo al indexar / recuperar, no en cada prompt.
- Gaps (año de fundación, contactos) quedan como “no publicado” en el MD
  en lugar de inventarse.

## Alternativas descartadas

- Vector DB cloud / LangChain: overhead y dependencia innecesaria.
- Inyectar el MD completo en el system prompt: choca con ADR-0015.
- Vectorizar Mongo: precios/cupos deben seguir tools live.
