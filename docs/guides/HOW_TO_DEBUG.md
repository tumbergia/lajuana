# How to debug

## Backend

### Logs

```bash
# Ver logs en tiempo real
make api-dev  # uvicorn con --reload, logs en consola

# Logging estructurado (JSON)
LOG_FORMAT=json make api-dev
```

Niveles:
- `logger.exception()` — errores con traceback
- `logger.warning()` — issues recuperables
- `logger.info()` — lifecycle (requests, tool calls)
- `logger.debug()` — detalle interno (desactivado por defecto)

Campos custom: `trace_id`, `conversation_id`, `channel`, `tool_name`, `latency_ms`.

### Tests

```bash
# Test específico
cd apps/api && python -m pytest tests/test_mi_archivo.py -v

# Test con prints
cd apps/api && python -m pytest tests/test_mi_archivo.py -vvs

# Coverage
cd apps/api && python -m pytest --cov=app --cov-report=term
```

### MCP inspector

```bash
make api-mcp
# Servidor MCP standalone en puerto configurado
# Usar audit_tools.py para probar tools
python scripts/audit_tools.py --verbose
```

### Errores comunes

| Error | Causa | Fix |
|-------|-------|-----|
| `ValidationError: reservation_id` | PydanticObjectId sin str() | `str(doc.reservation_id)` en mapper |
| `DuplicateKeyError` | Violación de índice único | Usar `update` con `upsert` o catch + ApiError |
| `NameError: document_models` | Variable no extraída en db.py | Extraer lista a variable antes de init_beanie |
| `AttributeError: 'str' object has no attribute 'isoformat'` | start_time es string, no time | Usar `start_time` directamente |
| `GeminiResourceExhausted` | Cuota excedida | Esperar minutos, rotar API key |
| `InvalidSignatureError` | JWT secret cambiado | Volver al secret anterior o re-login |

## Mobile

### Flutter DevTools

```bash
make mobile-run  # luego 'd' para DevTools en terminal
```

Features útiles:
- Inspector widget tree
- Timeline (rendimiento, builds)
- Logging (debugPrint)
- Memory

### Debug en dispositivo

```dart
// debugPrint se muestra en consola
debugPrint('State changed: $_state');

// Flutter dev tools overlay
// import 'package:flutter/rendering.dart';
// debugPaintSizeEnabled = true;
```

### Análisis

```bash
make mobile-analyze  # 0 errores requerido
```

### Problems comunes

| Problema | Causa | Fix |
|----------|-------|-----|
| `const` con deferred import | Widget de librería diferida | Sacar `const` |
| sqflite `DatabaseException` | Write concurrente | Usar `databaseExecutor` |
| Icono no se ve | Weight no soportada | Verificar en `material_symbols_icons` |
| `Method not found: '_statusTone'` | Helper fuera de clase | Mover helper a top-level o static dentro de clase |
