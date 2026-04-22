"""Bloques reutilizables de documentación OpenAPI."""

from app.schemas.common import ApiErrorResponse

COMMON_AUTH_RESPONSES = {
    401: {
        "model": ApiErrorResponse,
        "description": "No autenticado, token inválido o sesión expirada.",
    },
    403: {
        "model": ApiErrorResponse,
        "description": "El usuario autenticado no tiene permisos para ejecutar esta acción.",
    },
    422: {
        "model": ApiErrorResponse,
        "description": "La solicitud contiene datos inválidos o incompletos.",
    },
}
