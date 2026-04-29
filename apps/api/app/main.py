from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.lifespan import lifespan

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
        {"name": "Chat", "description": "Orquestador conversacional por rol con RAG y booking."},
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
