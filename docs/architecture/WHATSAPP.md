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
  participant T as STT (faster-whisper)

  W->>M: Envía mensaje
  M->>I: POST /whatsapp/webhook
  I->>I: Validate + verify signature

  alt Texto / botón / interactive
    I->>B: Buffer message (10s debounce)
    B-->>I: 200 OK
  else Audio
    I->>T: download + transcribe (auto-detect lang)
    T-->>I: {text, language, language_probability}
    alt Idioma detectado en catálogo
      I->>O: orchestrator.ask(audio_language=lang)
      O-->>I: AskResponse
      I->>P: Send response
      P->>M: POST /messages
    else Idioma NO soportado
      I->>P: Send unsupported_language_message
      P->>M: POST /messages
    end
  end

  loop Every 2s (text path)
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
| `IngestionService` | `channels/whatsapp/ingestion_service.py` | Recibir webhook, validar, transcribir audio, enrutar |
| `Normalizer` | `channels/whatsapp/normalizer.py` | Normalizar payload |
| `Parser` | `channels/whatsapp/parser.py` | Parsear payload |
| `Sender` | `channels/whatsapp/sender.py` | Enviar vía Meta API |
| `OutboundService` | `channels/whatsapp/outbound_service.py` | Orquestar envío |
| `MessageBufferService` | `conversations/services/message_buffer_service.py` | Debounce 10s, max 30s buffer (solo texto) |
| `ConversationScheduler` | `conversations/services/conversation_scheduler.py` | Background polling loop |
| `STTProvider` | `ai/providers/stt_provider.py` | faster-whisper con auto-detección multilingüe |

## Key features

- **Debounce**: mensajes de texto se bufferan 10s (max 30s) antes de procesar
- **Lock service**: previene procesamiento concurrente del mismo conversation_id
- **Webhook verification**: firma Meta verificada
- **Media download**: worker async para descargar imágenes/documentos
- **Audio directo**: audios se procesan sin pasar por el buffer para evitar
  doble respuesta. Si el STT detecta un idioma fuera del catálogo soportado
  (es/en/fr/de/it/ru/zh/ja), se responde con `unsupported_language_message`.
  Ver ADR-0013.

## Endpoints

| Método | Ruta | Propósito |
|--------|------|-----------|
| GET | `/whatsapp/webhook` | Meta verification |
| POST | `/whatsapp/webhook` | Recibir mensajes entrantes |
