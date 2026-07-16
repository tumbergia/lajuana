# ADR-0013: STT multilingüe (Whisper) y fix del crash de `phone` en el orchestrator

**Fecha:** 2026-07-15  
**Estado:** ✅ Aceptado  
**Complementa:** [0010 — Política de idioma del bot](0010-bot-language-policy.md)

## Contexto

Dos problemas relacionados detectados en producción:

### 1. Crash `UnboundLocalError: phone` al recibir audios

En `apps/api/app/ai/assistant/orchestrator.py:298` (línea anterior al fix),
el bloque `if explicit_request:` referenciaba la variable `phone` ANTES de
su asignación, que ocurría 35 líneas más abajo. Esto provocaba un crash
(`UnboundLocalError: cannot access local variable 'phone' where it is not
associated with a value`) en cualquier path de audio donde el usuario, en
el mismo turno o en un turno posterior, pidiera explícitamente un idioma.
El audio path en `ingestion_service.py` capturaba la excepción y dejaba al
bot sin responder.

### 2. STT monolingüe forzando alucinaciones severas

`apps/api/app/ai/providers/stt_provider.py:47` (versión anterior) invocaba
Whisper con `language="es"` hardcodeado. Esto significa que cualquier audio
NO español (chino, ruso, japonés, etc.) era forzado a decodificarse como
español, produciendo transcripciones sin sentido:

| Audio real | Transcripción reportada |
|---|---|
| `Wǒ xiǎng yùdìng` (zh: quiero reservar) | `Washington, U.T.` |
| Audio en ruso | `Please speak in English.` |

Con un modelo `base` (74M params) y `language="es"` forzado, Whisper
**alucinaba frases en inglés** cuando los fonemas no encajaban con el
vocabulario español. El usuario recibía galimatías y el bot no podía
procesar la intención.

Adicionalmente, el modelo `base` tiene capacidad multilingüe muy pobre
— `tiny`/`base` rinden mal en zh/ru/ja; `small` (244M) es el mínimo
aceptable para esos idiomas, `medium` (769M) es robusto y `large-v3`
es el ideal (requiere GPU).

## Decisión

### 1. Fix del crash de `phone`

Mover la resolución de `phone` (`request.from_phone or
getattr(session, "from_phone", None)`) **antes** de la política de idioma
en `orchestrator.ask()`. La rama `if explicit_request:` (que sincroniza
`holder_language` en reservas activas) ya puede usarla con seguridad.

**Verificación:** nuevo test
`tests/test_orchestrator_explicit_request_with_phone.py` que reproduce el
crash y valida que la sincronización se dispara correctamente.

### 2. STT multilingüe con auto-detección

**Cambios en `stt_provider.py`:**
- `language=settings.whisper_language` (None por default) en lugar de
  `language="es"`. Esto habilita la auto-detección nativa de Whisper.
- `condition_on_previous_text=False`: evita que un error de un segmento
  contamine el siguiente en audios largos (alucinación en cascada).
- `vad_filter=True`: corta silencios antes de transcribir, reduciendo
  alucinaciones en audios de WhatsApp (muchos silencios entre frases).
- Nueva firma `transcribe_audio(...) -> TranscriptionResult` con
  `text`, `language`, `language_probability`, `duration`. Antes retornaba
  solo `str`.

**Cambios en `config.py` + `.env.example`:**
- `WHISPER_MODEL_SIZE=small` (antes `base`). Tradeoff: ~244MB en RAM,
  ~2× más lento en CPU, pero soporte multilingüe confiable.
- `WHISPER_LANGUAGE=` (vacío = auto-detección). Documentado explícitamente
  por qué NO se debe forzar un código fijo.
- `WHISPER_BEAM_SIZE=5` extraído a variable.

### 3. Idioma detectado en el flujo de audio

**Cambios en `AskRequest`:** nuevo campo opcional `audio_language: str | None`
que propaga el idioma detectado por el STT al orchestrator.

**Cambios en `WhatsAppInboundEventDocument`:** nuevo campo
`transcription_language: str | None` que persiste el idioma detectado para
trazabilidad.

**Cambios en `ingestion_service.py`:**
- Si el STT detecta un idioma **fuera** de `SUPPORTED_RESPONSE_LANGUAGES`
  (`es, en, fr, de, it, ru, zh, ja`), el servicio responde con
  `unsupported_language_message` (mismo mensaje que cuando el usuario
  escribe en un idioma no soportado por texto) y **NO** invoca al
  orchestrator. Esto es consistente con ADR-0010.
- Si el idioma detectado **está** en el catálogo, el audio se procesa
  normalmente y `audio_language` se pasa al `AskRequest` para que el
  orchestrator pueda usarlo en el futuro (e.g. sugerir cambio de idioma).

### 4. Política de idioma del bot NO cambia

ADR-0010 sigue vigente: el bot **nace en español, no auto-detecta idioma
del texto y solo cambia por override explícito**. Lo que cambia con este
ADR es:

- El STT ahora detecta el idioma del audio de forma nativa (esto es
  interno al modelo, no afecta la política).
- Si el idioma detectado está fuera del catálogo, se informa al usuario.
- Si el idioma detectado está dentro del catálogo, se procesa
  normalmente y el bot sigue respondiendo en `session.language` (no
  cambiamos automáticamente al idioma del audio — eso sería una
  violación de ADR-0010).

## Alternativas consideradas

- **Whisper API en la nube (OpenAI, AssemblyAI).** Descartado: introduce
  dependencia externa, costo por minuto y latencia adicional. El caso de
  uso (audios cortos de WhatsApp < 30s) no justifica salir del inference
  local.
- **Whisper `large-v3` con GPU.** Descartado: requiere infraestructura
  GPU dedicada. `small` en CPU da calidad suficiente para el caso.
- **Mantener `base` y agregar detección de idioma post-hoc con
  `langdetect`.** Descartado: la calidad de transcripción en zh/ru/ja
  con `base` es tan baja que `langdetect` no tiene señal suficiente
  para clasificar el texto resultante. La auto-detección nativa de
  Whisper es estrictamente superior.
- **Auto-cambiar `session.language` al idioma detectado en audio.**
  Descartado: rompe ADR-0010 ("solo override explícito"). Si en el
  futuro queremos esto, debe ser una nueva decisión con opt-in del
  usuario.

## Consecuencias

- Audios en chino, ruso, japonés, francés, alemán, italiano e inglés se
  transcriben correctamente (con `small`).
- Audios en idiomas no soportados (coreano, portugués, holandés, etc.)
  reciben una respuesta informativa con los idiomas disponibles.
- El bot no se queda en silencio cuando un audio produce transcripción
  vacía o con caracteres no procesables.
- La política de idioma del bot (ADR-0010) se mantiene intacta.
- Memoria RAM: ~500MB adicionales en el proceso (modelo `small` cargado
  una sola vez en singleton global).
- Latencia: ~1-3s adicionales por audio de 30s en CPU. Aceptable para
  WhatsApp.

## Trazabilidad

- `apps/api/app/ai/assistant/orchestrator.py` (fix `phone`)
- `apps/api/app/ai/providers/stt_provider.py` (auto-detección, `vad_filter`)
- `apps/api/app/core/config.py` (defaults `small` + auto-detect)
- `apps/api/.env.example` (documentación de variables)
- `apps/api/app/services/audio_transcription_service.py` (retorna
  `TranscriptionResult`)
- `apps/api/app/channels/whatsapp/ingestion_service.py` (idioma no
  soportado → `unsupported_language_message`)
- `apps/api/app/schemas/ask.py` (campo `audio_language`)
- `apps/api/app/conversations/documents.py` (campo `transcription_language`)
- Tests:
  - `tests/test_orchestrator_explicit_request_with_phone.py`
  - `tests/test_stt_provider.py`
  - `tests/test_ingestion_audio_language.py`
