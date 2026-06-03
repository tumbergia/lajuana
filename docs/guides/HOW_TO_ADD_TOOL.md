# How to add an MCP tool

## Paso a paso

### 1. Implementar la función tool

En `apps/api/app/ai/mcp/tools/` (crear o modificar archivo):

```python
# apps/api/app/ai/mcp/tools/mi_tool.py
from app.schemas.assistant_plan import ToolArgs, ToolResultResponse

async def mi_tool(
    arg1: str,
    arg2: int | None = None,
    conversation_id_for_log: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
) -> dict:
    """Descripción de lo que hace la tool."""
    try:
        result = await some_service.do_something(arg1, arg2)
        return {"response": f"Operación exitosa: {result}", "data": result}
    except Exception as exc:
        return {"error": str(exc), "trace_id": trace_id}
```

Parámetros estándar (opcionales pero recomendados):
- `conversation_id_for_log`
- `trace_id`
- `conversation_turn_id`

### 2. Registrar en el registry

En `apps/api/app/ai/mcp/__init__.py`:

```python
_TOOLS: dict[str, object] = {
    # ... existing tools
    "mi_tool": tools.mi_tool,
}
```

Si creaste un nuevo archivo, agregar el import al inicio:
```python
from app.ai.mcp.tools import mi_tool as tools_mi_tool
# Y en _TOOLS:
_TOOLS = {
    "mi_tool": tools_mi_tool.mi_tool,
    # ...
}
```

### 3. Agregar al planificador (si es admin tool)

En `apps/api/app/ai/assistant/planner.py`:

- Si es admin tool: agregar keyword en `_ADMIN_TOOL_CATEGORIES` y descripción en `_ADMIN_TOOL_DESCRIPTIONS`
- Si es client tool: automáticamente incluida por el planner

### 4. Política de permisos (si aplica)

En `apps/api/app/ai/assistant/policy.py`:

Agregar la tool al set correspondiente:
- `CLIENT_TOOLS` — accesible por cualquier canal
- `GUIDE_TOOLS` — accesible por guías
- `ADMIN_TOOLS` — solo admin_api
- `READ_TOOLS` — solo lectura (sin restricción de escritura)
- `LIMITED_WRITE_TOOLS` — escritura limitada
- `WRITE_TOOLS` — escritura completa
- `CRITICAL_TOOLS` — siempre denegadas

### 5. Confirmación (si es destructiva)

En `apps/api/app/ai/assistant/orchestrator.py`:

Agregar tool name a `WRITE_TOOLS_REQUIRING_CONFIRMATION` si necesita confirmación del usuario antes de ejecutarse.

### 6. Pruebas

```bash
# Usar el MCP inspector
make api-mcp
# Enviar request de prueba
python scripts/audit_tools.py --verbose
```

## Checklist

- [ ] Función tool implementada con return type `dict`
- [ ] Registrada en `__init__.py` de MCP
- [ ] Si es admin: agregada a planner.py keywords + descripciones
- [ ] Política actualizada en policy.py
- [ ] Si es write tool: agregada a WRITE_TOOLS_REQUIRING_CONFIRMATION
- [ ] Tool probada con audit_tools.py
