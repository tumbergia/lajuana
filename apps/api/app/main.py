from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.lifespan import lifespan

app = FastAPI(
    title=settings.app_name,
    summary="Backend centralizado para reservas, operación y trazabilidad.",
    description=(
        "API central de La Juana para gestión de usuarios, reservas, participantes, "
        "pagos, asignaciones y bitácora operativa. La reserva confirmable es la "
        "entidad principal del sistema."
    ),
    version=settings.app_version,
    contact={"name": "Equipo La Juana"},
    openapi_tags=[
        {"name": "Authentication", "description": "Autenticación y sesión actual."},
        {"name": "Users", "description": "Gestión administrativa de usuarios internos."},
        {"name": "Experiences", "description": "Catálogo de experiencias."},
        {"name": "Schedules", "description": "Fechas operativas y disponibilidad."},
        {"name": "Reservations", "description": "Flujo central de reservas."},
        {"name": "Participants", "description": "Participantes de una reserva."},
        {"name": "Configuration", "description": "Configuración sensible del sistema."},
        {"name": "Equines", "description": "Gestión de equinos para operación."},
        {"name": "Saddles", "description": "Gestión de sillas operativas."},
        {"name": "Assignments", "description": "Asignaciones operativas."},
        {"name": "Service Logs", "description": "Bitácora del servicio."},
        {"name": "Providers", "description": "Proveedores externos."},
        {"name": "Policies", "description": "Pólizas asociadas a reservas."},
        {"name": "health", "description": "Salud y diagnóstico."},
        {"name": "diagnostics", "description": "Diagnósticos técnicos."},
    ],
    lifespan=lifespan,
)
register_error_handlers(app)
app.include_router(api_router)
