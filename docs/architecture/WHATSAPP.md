# WhatsApp Channel

Meta Cloud API. Webhook → Ingestion → AI Assistant → Outbound.

## Flow

```mermaid
sequenceDiagram
  participant W as WhatsApp User
  participant M as Meta API
  participant I as IngestionService
  participant B as MessageBuffer
  participant S as ConversationScheduler
  participant O as AssistantOrchestrator
  participant P as OutboundService

  W->>M: Envía mensaje
  M->>I: POST /whatsapp/webhook
  I->>I: Validate + verify signature
  I->>B: Buffer message (10s debounce)
  B-->>I: 200 OK

  loop Every 2s
    S->>B: Poll for ready messages
    B-->>S: Message batch
    S->>O: orchestrator.ask()
    O-->>S: AskResponse
    S->>P: Send response
    P->>M: POST /messages
    M->>W: Mensaje entregado
  end
```

## Components

| Componente | Archivo | Responsabilidad |
|-----------|---------|----------------|
| `IngestionService` | `channels/whatsapp/ingestion_service.py` | Recibir webhook, validar, encolar |
| `Normalizer` | `channels/whatsapp/normalizer.py` | Normalizar payload |
| `Parser` | `channels/whatsapp/parser.py` | Parsear payload |
| `Sender` | `channels/whatsapp/sender.py` | Enviar vía Meta API |
| `OutboundService` | `channels/whatsapp/outbound_service.py` | Orquestar envío |
| `MessageBufferService` | `conversations/services/message_buffer_service.py` | Debounce 10s, max 30s buffer |
| `ConversationScheduler` | `conversations/services/conversation_scheduler.py` | Background polling loop |

## Key features

- **Debounce**: mensajes entrantes se bufferan 10s (max 30s) antes de procesar
- **Lock service**: previene procesamiento concurrente del mismo conversation_id
- **Webhook verification**: firma Meta verificada
- **Media download**: worker async para descargar imágenes/documentos

## Endpoints

| Método | Ruta | Propósito |
|--------|------|-----------|
| GET | `/whatsapp/webhook` | Meta verification |
| POST | `/whatsapp/webhook` | Recibir mensajes entrantes |
