# Prueba RAG - Agente WhatsApp Operativo

Implementacion del agente conversacional operativo de La Juana para WhatsApp,
con uso de tools reales del backend y RAG asistido por Gemma 4.

## Componentes

- `whatsapp_operational_agent.py`: cerebro conversacional + tools + RAG.
- `whatsapp_cloud_webhook.py`: webhook FastAPI para WhatsApp Cloud API.
- `.env.example`: variables para backend, Gemma y Meta.

## Reglas de negocio que cumple

- Nunca confirma reserva sin backend.
- Nunca confirma cupos sin consultar disponibilidad real.
- Nunca valida pago sin comprobante registrado.
- Solicita datos obligatorios para crear/continuar reserva.
- Escala a humano ante conflicto operativo o error backend.

## 1) Preparar Gemma 4 como modelo RAG

Puedes usar LM Studio u otro servidor OpenAI-compatible local.

### Opcion A: LM Studio (recomendada)

1. Descarga y abre Gemma 4 Instruct.
2. En LM Studio, inicia servidor local en formato OpenAI API.
3. ⚠️ **IMPORTANTE**: Desactiva "Extended Thinking" o "Reasoning" en las settings del modelo:
   - Ve a "Model Settings" en LM Studio
   - Busca "Enable extended thinking", "Enable reasoning", o similar
   - **Desactívalo completamente** para evitar loops infinitos de razonamiento
4. Verifica endpoint (ejemplo): `http://127.0.0.1:1234/v1`.
5. Configura en `.env`:
   - `LJ_LLM_ENABLED=true`
   - `LJ_LLM_BASE_URL=http://127.0.0.1:1234/v1`
   - `LJ_LLM_MODEL=gemma-4-27b-it` (o el nombre exacto que exponga tu servidor)

### Opcion B: otro proveedor OpenAI-compatible

- Solo debes cambiar `LJ_LLM_BASE_URL`, `LJ_LLM_MODEL` y `LJ_LLM_API_KEY` si aplica.

## 2) Variables de entorno

Crea un `.env` en `apps/api/prueba-rag` basado en `.env.example`.

Variables clave:

- Backend:
  - `LJ_API_BASE_URL=http://127.0.0.1:8000/api/v1`
  - `LJ_AGENT_EMAIL=...`
  - `LJ_AGENT_PASSWORD=...`
- RAG con Gemma:
  - `LJ_LLM_ENABLED=true`
  - `LJ_LLM_BASE_URL=.../v1`
  - `LJ_LLM_MODEL=...`
  - `LJ_LLM_TIMEOUT_SECONDS=600` (tiempo maximo para inferencia)
  - `LJ_LLM_CIRCUIT_BREAKER_THRESHOLD=3` (fallos consecutivos antes de deshabilitar LLM)
- WhatsApp Cloud:
  - `WA_VERIFY_TOKEN=...`
  - `WA_ACCESS_TOKEN=...`
  - `WA_PHONE_NUMBER_ID=...`

## 3) Correr backend de La Juana

Desde `apps/api`:

```bash
uvicorn app.main:app --reload
```

## 4) Correr webhook WhatsApp local

En otra terminal, desde `apps/api`:

```bash
uvicorn whatsapp_cloud_webhook:app --app-dir prueba-rag --host 0.0.0.0 --port 8080
```

## 5) Exponer webhook a internet (Meta necesita URL publica)

Ejemplo con ngrok:

```bash
ngrok http 8080
```

Obtendras una URL tipo `https://abc123.ngrok-free.app`.

Webhook URL en Meta:

- `https://abc123.ngrok-free.app/webhook`

## 6) Configurar WhatsApp Cloud en Meta

Necesitas acceso a plataforma Meta Developers y WhatsApp Cloud API.

1. Crear app en Meta Developers.
2. Agregar producto WhatsApp.
3. Obtener:
   - Temporary/Permanent Access Token (`WA_ACCESS_TOKEN`)
   - Phone Number ID (`WA_PHONE_NUMBER_ID`)
4. Configurar Webhook:
   - Callback URL: `https://.../webhook`
   - Verify Token: el mismo valor de `WA_VERIFY_TOKEN`
5. Suscribir evento `messages`.
6. Agregar tu numero como tester en sandbox de WhatsApp Cloud.

## 7) Probar directo en WhatsApp

1. Escribe al numero de prueba de WhatsApp Cloud.
2. El webhook recibe el mensaje y responde con el agente.
3. Veras trazabilidad en `conversation_trace.jsonl`.

## Comandos utiles de prueba

Para prueba local sin WhatsApp:

```bash
python prueba-rag/whatsapp_operational_agent.py --message "Quiero reservar para 3 personas el 2026-05-10"
```

Para pasar payload JSON de comprobante/participante por WhatsApp en pruebas:

- Comprobante: mensaje con prefijo `/proof {json}`
- Participante: mensaje con prefijo `/participant {json}`

## Limitaciones actuales

### Circuit Breaker para LLM

Si el modelo LLM (Gemma, OpenAI, etc.) falla o timeout repetidamente:

- El agente cuenta fallos consecutivos en LLM.
- Despues de `LJ_LLM_CIRCUIT_BREAKER_THRESHOLD` fallos (por defecto 3), deshabilita LLM.
- Vuelve a usar RAG léxico (busqueda de términos en documentacion local).
- Resultado: usuario siempre recibe respuesta, evitando timeout silencioso.

Esto evita que una mala configuración del modelo (bajo recursos, timeout corto, etc.) deje
al usuario sin respuesta.

### Fallback a RAG léxico

Cuando el LLM está deshabilitado o falla una consulta individual:

- Se intenta responder con busqueda léxica en `docs/` y archivos README.
- Si no hay respuesta útil, el agente devuelve mensaje de escalada a humano.

Este comportamiento es defensivo: mejor respuesta simple que nada.

### Otras limitaciones

- WhatsApp Cloud no envia `content_base64` automaticamente para archivos; ese flujo en esta base
  requiere integracion adicional de descarga de media + conversion base64.
- Esta implementacion es operativa para pruebas, no un despliegue productivo completo.

## Troubleshooting

### Problema: El modelo responde muy lentamente o entra en loop de razonamiento

**Síntoma**: Logs muestran "Accumulated 184 tokens in reasoning content", "Accumulated 185 tokens..." repitiendo.

**Causa**: Gemma 4 tiene "Extended Thinking" habilitado, causando razonamiento infinito interno.

**Solución**:

1. **En LM Studio**, ve a Model Settings del modelo Gemma 4.
2. Desactiva cualquier opción llamada:
   - "Extended Thinking"
   - "Enable Reasoning"
   - "Internal Monologue"
   - Similar
3. Reinicia el servidor LLM.
4. Reinicia el webhook.

**Alternativa rápida**: Desactiva LLM temporalmente en `.env`:
```env
LJ_LLM_ENABLED=false
```
El agente usará RAG léxico (búsqueda en documentos locales) - funciona al instante.

### Problema: Timeout después de esperar 30 segundos

**Causa**: El modelo LLM no responde dentro del tiempo límite.

**Solución**:

1. Verifica que el servidor LLM esté activo: `http://127.0.0.1:1234`
2. Prueba manualmente:
   ```bash
   curl -X POST http://127.0.0.1:1234/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model":"gemma-4-e2b","messages":[{"role":"user","content":"Hola"}],"max_completion_tokens":100}'
   ```
3. Si sigue lento, considera:
   - Reducir `LJ_LLM_TIMEOUT_SECONDS` aún más (ej: 15)
   - Cambiar a un modelo más pequeño
   - Deshabilitar `LJ_LLM_ENABLED=false`

### Problema: No recibo respuesta del webhook

**Causa**: El agente falló internamente o timeout.

**Solución**:

1. Revisa `conversation_trace.jsonl` para ver qué intent detectó.
2. Revisa `webhook_events.jsonl` para ver qué mensaje llegó.
3. Mira los logs de la consola del webhook (busca "[ERROR]" o "[Circuit Breaker]").
4. Si ves timeout repetido, el circuit breaker deshabilitará LLM automáticamente.
5. Reinicia el webhook para resetear el contador de fallos.

### Problema: El agente siempre responde desde RAG léxico, nunca usa LLM

**Causa**: Circuit breaker está activo (3+ fallos consecutivos de LLM).

**Solución**:

1. Revisa que el servidor LLM esté corriendo.
2. Mira el timeout configurado: `LJ_LLM_TIMEOUT_SECONDS` (si es muy corto, aumenta).
3. Reinicia el webhook para resetear los contadores de fallos.
4. Si sigue sin funcionar, desactiva y reactiva `LJ_LLM_ENABLED`.