# System Overview

```mermaid
C4Context
  title Sistema La Juana — Containers

  Person(cliente, "Cliente", "WhatsApp / Web")
  Person(admin, "Admin", "Mobile app")
  Person(guia, "Guía", "Mobile app")

  System_Boundary(lajuana, "La Juana System") {
    Container(mobile, "Mobile App", "Flutter + SQLite", "Punto de operación principal")
    Container(api, "API Server", "FastAPI + Beanie/MongoDB", "Fuente de verdad")
    Container(ai, "AI Assistant", "Gemini + MCP Tools", "Planificador conversacional")
    ContainerDb(mongo, "MongoDB", "Document DB", "Datos persistentes")
    ContainerDb(sqlite, "SQLite", "Local DB", "Cache offline")
  }

  System_Ext(whatsapp, "WhatsApp API", "Meta Cloud API")
  System_Ext(s3, "S3 Storage", "Archivos multimedia")

  Rel(cliente, whatsapp, "Mensajes")
  Rel(whatsapp, api, "Webhook")
  Rel(admin, mobile, "Opera")
  Rel(guia, mobile, "Opera")
  Rel(mobile, api, "REST /api/v1", "Sync")
  Rel(api, mongo, "Beanie ODM")
  Rel(mobile, sqlite, "sqflite")
  Rel(api, ai, "LLM call")
  Rel(api, s3, "boto3")
  Rel(api, whatsapp, "Outbound")
```

## Capas del sistema

```mermaid
flowchart TD
  subgraph Frontend["Flutter App (apps/mobile/)"]
    UI["UI Layer<br/>Screens + Widgets"]
    CT["Controllers<br/>ChangeNotifier + ActionState"]
    INF["Infrastructure<br/>API Clients + SQLite + Mappers"]
    DOM["Domain<br/>Models + Repository Interfaces"]
  end

  subgraph Backend["API Server (apps/api/)"]
    EP["Endpoints<br/>FastAPI Routers (x25)"]
    SV["Services<br/>Business Logic (x25+)"]
    DOC["Documents<br/>Beanie ODM (x30+)"]
  end

  subgraph Packages["Shared Packages (packages/)"]
    MC["mobile_core<br/>Utils"]
    MD["mobile_domain<br/>Domain Models"]
    MUI["mobile_ui<br/>Widgets"]
    MM["mobile_mocks<br/>Fakes"]
  end

  UI --> CT
  CT --> INF
  INF --> DOM
  DOM --> MD
  UI --> MUI
  CT --> MC
  INF --> EP
  EP --> SV
  SV --> DOC
  DOC --> MongoDB
  INF --> SQLite
```

## Flujo de datos principal

```mermaid
sequenceDiagram
  participant U as Usuario (Mobile)
  participant C as Controller
  participant R as Repository
  participant A as API
  participant S as Service
  participant D as MongoDB

  U->>C: Acción (tap, scroll)
  C->>C: ActionState.loading()
  C->>R: domain method
  R->>A: HTTP request
  A->>S: endpoint → service
  S->>D: Beanie query
  D-->>S: document
  S-->>A: response
  A-->>R: DTO
  R->>R: mapper DTO→domain
  R->>R: cache in SQLite
  R-->>C: domain model
  C->>C: ActionState.success()
  C-->>U: UI rebuild
```

## Stack tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Backend framework | FastAPI | >=0.115 |
| ODM | Beanie (async MongoDB) | 1.x |
| Validación | Pydantic v2 | — |
| Auth | bcrypt + PyJWT (HS256) | — |
| AI | google-genai (Gemini 2.5) | — |
| Storage | boto3 (S3) o local | — |
| Backend tests | pytest + mongomock | — |
| Frontend | Flutter (Dart 3.11) | channel stable |
| State | ValueNotifier + ChangeNotifier | — |
| Local DB | sqflite (SQLite) | — |
| Icons | material_symbols_icons | — |
| Workspace | Dart pub workspace | — |

## Monorepo

```
/
├── apps/
│   ├── api/          # FastAPI (Python)
│   └── mobile/       # Flutter (Dart)
├── packages/
│   ├── mobile_core/  # Utilidades base
│   ├── mobile_domain/# Modelos + interfaces
│   │   └── gen/      # Generados desde OpenAPI
│   ├── mobile_ui/    # Widgets reusables
│   └── mobile_mocks/ # Fakes para testing
├── docs/             # Documentación
├── scripts/          # Scripts de utilidad
├── tools/            # Codegen
└── dev/playground/   # Dev screens (debug only)
```
