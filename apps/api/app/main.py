from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.endpoints.whatsapp import bare_router as whatsapp_bare_router
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.lifespan import lifespan

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title=settings.app_name,
    summary="Backend centralizado para reservas, operacion y trazabilidad.",
    description=(
        "API central de La Juana para gestion de usuarios, reservas, participantes, "
        "pagos, asignaciones y bitacora operativa. La reserva confirmable es la "
        "entidad principal del sistema."
    ),
    version=settings.app_version,
    contact={"name": "Equipo La Juana"},
    openapi_tags=[
        {"name": "Autenticacion", "description": "Autenticacion y sesion actual."},
        {"name": "Assistant", "description": "Planner Gemini + tools + policy."},
        {"name": "Usuarios", "description": "Gestion administrativa de usuarios internos."},
        {"name": "Experiencias", "description": "Catalogo de experiencias."},
        {"name": "Fechas operativas", "description": "Fechas operativas y disponibilidad."},
        {"name": "Reservas", "description": "Flujo central de reservas."},
        {"name": "Participantes", "description": "Participantes de una reserva."},
        {"name": "Configuracion", "description": "Configuracion sensible del sistema."},
        {"name": "Equinos", "description": "Gestion de equinos para operacion."},
        {"name": "Sillas", "description": "Gestion de sillas operativas."},
        {"name": "Asignaciones", "description": "Asignaciones operativas."},
        {"name": "Bitacora", "description": "Bitacora del servicio."},
        {"name": "Proveedores", "description": "Proveedores externos."},
        {"name": "Polizas", "description": "Polizas asociadas a reservas."},
        {"name": "Comprobantes de pago", "description": "Consulta y validacion de comprobantes."},
        {
            "name": "WhatsApp",
            "description": "Webhook y orquestacion conversacional publica para WhatsApp.",
        },
        {"name": "Sync", "description": "Sincronizacion incremental offline-first."},
        {"name": "Files", "description": "Inicializacion y consolidacion de uploads."},
        {"name": "health", "description": "Salud y diagnostico."},
        {"name": "diagnostics", "description": "Diagnosticos tecnicos."},
    ],
    lifespan=lifespan,
)
register_error_handlers(app)


def _parse_cors_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.cors_allowed_origins),
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(whatsapp_bare_router)


@app.get("/formulario-participantes", include_in_schema=False)
async def participant_form_page() -> HTMLResponse:
    html_path = STATIC_DIR / "participant_form.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Formulario no disponible</h1>", status_code=503)
    content = html_path.read_text(encoding="utf-8")
    return HTMLResponse(content)


@app.get("/formulario-participantes/", include_in_schema=False)
async def participant_form_page_slash() -> HTMLResponse:
    return await participant_form_page()
