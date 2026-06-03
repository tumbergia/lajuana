# Documentación — La Juana

Mapa de navegación. Cada archivo tiene un propósito único.

## 🚀 Primeros pasos

| Documento | Para qué |
|-----------|----------|
| [`QUICKSTART.md`](QUICKSTART.md) | De git clone a servidor corriendo en 5 minutos |
| `AGENTS.md` (raíz) | Guía para asistentes/colaboradores |
| `SKILLS.md` (raíz) | Capacidades del repositorio |

## 🏛️ Arquitectura

| Documento | Para qué |
|-----------|----------|
| [`architecture/OVERVIEW.md`](architecture/OVERVIEW.md) | Diagrama del sistema completo, containers, data flow |
| [`architecture/BACKEND.md`](architecture/BACKEND.md) | Backend: routers, services, documents, DI, migrations |
| [`architecture/FRONTEND.md`](architecture/FRONTEND.md) | Flutter: módulos, controllers, repos, packages |
| [`architecture/DATABASE.md`](architecture/DATABASE.md) | MongoDB: colecciones, índices, migraciones, seeds |
| [`architecture/SYNC.md`](architecture/SYNC.md) | Protocolo offline-first |
| [`architecture/AI.md`](architecture/AI.md) | Pipeline del asistente: planner→policy→tools |
| [`architecture/WHATSAPP.md`](architecture/WHATSAPP.md) | Canal WhatsApp: webhook, ingestion, outbound |

## 📡 API Reference

| Documento | Para qué |
|-----------|----------|
| [`api/ENDPOINTS.md`](api/ENDPOINTS.md) | Todos los endpoints por router |
| [`api/ERRORS.md`](api/ERRORS.md) | Catálogo de códigos de error |
| [`api/TOOLS.md`](api/TOOLS.md) | Referencia de MCP tools |

## 📱 Mobile / Flutter

| Documento | Para qué |
|-----------|----------|
| [`mobile/ARCHITECTURE.md`](mobile/ARCHITECTURE.md) | Clean architecture, módulos, DI |
| [`mobile/STATE.md`](mobile/STATE.md) | State management pattern |
| [`mobile/ROUTING.md`](mobile/ROUTING.md) | Routing, shell, auth guard |
| [`mobile/WIDGETS.md`](mobile/WIDGETS.md) | Catálogo de widgets y contribution guide |
| [`mobile/OFFLINE.md`](mobile/OFFLINE.md) | Offline-first: SQLite, cache, fallback |
| [`mobile/TESTS.md`](mobile/TESTS.md) | Testing patterns y cómo testear |

## 📐 Convenciones

| Documento | Para qué |
|-----------|----------|
| [`conventions/BACKEND.md`](conventions/BACKEND.md) | Python: ruff, naming, imports, services |
| [`conventions/FRONTEND.md`](conventions/FRONTEND.md) | Dart: análisis, naming, widgets, estado |
| [`conventions/GIT.md`](conventions/GIT.md) | Git: branches, commits, PR flow |
| [`conventions/ARCHITECTURE.md`](conventions/ARCHITECTURE.md) | Principios cross-cutting |

## ⚖️ ADRs

| Documento | Estado |
|-----------|--------|
| [`decisions/README.md`](decisions/README.md) | Índice de todas las decisiones |
| [`decisions/0001-monorepo.md`](decisions/0001-monorepo.md) | ✅ Aceptado |
| [`decisions/0002-design-system.md`](decisions/0002-design-system.md) | ✅ Aceptado |
| [`decisions/0003-voice.md`](decisions/0003-voice.md) | 🟡 Prototipo |
| [`decisions/0004-mobile-ui-extract.md`](decisions/0004-mobile-ui-extract.md) | ⏳ Postergado |
| [`decisions/0005-chatbot-pipeline.md`](decisions/0005-chatbot-pipeline.md) | ✅ Aceptado |
| [`decisions/0006-list-detail-contract.md`](decisions/0006-list-detail-contract.md) | ✅ Aceptado |
| [`decisions/0007-holder-data.md`](decisions/0007-holder-data.md) | ✅ Aceptado |
| [`decisions/0008-offline-sync.md`](decisions/0008-offline-sync.md) | ✅ Aceptado |
| [`decisions/0009-auth-network.md`](decisions/0009-auth-network.md) | ✅ Aceptado |

## 🛠️ Guías prácticas

| Documento | Para qué |
|-----------|----------|
| [`guides/HOW_TO_ADD_ENDPOINT.md`](guides/HOW_TO_ADD_ENDPOINT.md) | Paso a paso: nuevo endpoint |
| [`guides/HOW_TO_ADD_TOOL.md`](guides/HOW_TO_ADD_TOOL.md) | Paso a paso: nuevo MCP tool |
| [`guides/HOW_TO_ADD_WIDGET.md`](guides/HOW_TO_ADD_WIDGET.md) | Paso a paso: nuevo widget reusable |
| [`guides/HOW_TO_DEBUG.md`](guides/HOW_TO_DEBUG.md) | Patrones de debugging |
| [`guides/HOW_TO_DEPLOY.md`](guides/HOW_TO_DEPLOY.md) | Despliegue y CI/CD |
