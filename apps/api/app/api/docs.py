"""Documentación centralizada de endpoints para OpenAPI."""

from typing import TypedDict

from app.api.business_errors import BUSINESS_ERROR_CASES, ENDPOINT_BUSINESS_CASES
from app.schemas.common import ApiErrorResponse


class EndpointDoc(TypedDict):
    summary: str
    description: str
    permissions: list[str]
    responses: dict[int, str]
    error_codes: list[str]
    service_docstring: str


ERROR_CODE_CONTRACT_RULE = "Frontend y tests dependen de error_codes, no del texto del mensaje."


ENDPOINT_DOCS: dict[str, EndpointDoc] = {
    "auth_register": {
        "summary": "Registrar usuario público",
        "description": (
            "Registra una cuenta de usuario público en estado unassigned. "
            "No asigna rol operativo ni privilegios administrativos."
        ),
        "permissions": [],
        "responses": {
            201: "Usuario registrado correctamente.",
            409: "Ya existe un usuario con el mismo correo.",
            422: "La solicitud contiene datos inválidos o incompletos.",
        },
        "error_codes": ["user.email_already_exists", "common.validation_error"],
        "service_docstring": "Registra una cuenta pública sin rol operativo.",
    },
    "auth_login": {
        "summary": "Iniciar sesión",
        "description": (
            "Autentica un usuario interno activo y retorna token de acceso con "
            "su contexto operativo."
        ),
        "permissions": [],
        "responses": {
            200: "Sesión iniciada correctamente.",
            401: "Credenciales inválidas o usuario inactivo.",
            422: "La solicitud contiene datos inválidos o incompletos.",
        },
        "error_codes": [
            "auth.invalid_credentials",
            "auth.inactive_user",
            "common.validation_error",
        ],
        "service_docstring": "Autentica por correo y contraseña contra hash persistido.",
    },
    "auth_refresh": {
        "summary": "Refrescar token",
        "description": "Renueva la sesión usando un refresh token válido.",
        "permissions": [],
        "responses": {200: "Token renovado correctamente.", 401: "Refresh token inválido."},
        "error_codes": ["auth.invalid_token"],
        "service_docstring": "Valida refresh token y emite nuevo access token.",
    },
    "auth_logout": {
        "summary": "Cerrar sesión",
        "description": "Cierra la sesión actual del usuario autenticado.",
        "permissions": ["auth.self.read"],
        "responses": {200: "Sesión cerrada correctamente.", 401: "Token ausente o inválido."},
        "error_codes": ["auth.unauthorized", "auth.invalid_token", "auth.expired_token"],
        "service_docstring": "Invalida el refresh token asociado a la sesión.",
    },
    "auth_change_password": {
        "summary": "Cambiar contraseña",
        "description": ("Cambia la contraseña del usuario autenticado validando la clave actual."),
        "permissions": ["auth.self.update_password"],
        "responses": {
            200: "Contraseña actualizada correctamente.",
            400: "La contraseña actual no coincide.",
            401: "Token ausente, inválido o cuenta inactiva.",
            422: "La solicitud contiene datos inválidos o incompletos.",
        },
        "error_codes": [
            "auth.password_mismatch",
            "auth.inactive_user",
            "auth.unauthorized",
            "auth.invalid_token",
            "auth.expired_token",
            "common.validation_error",
        ],
        "service_docstring": "Valida contraseña vigente y persiste nuevo hash.",
    },
    "auth_me": {
        "summary": "Consultar sesión actual",
        "description": "Retorna identidad operativa del usuario autenticado.",
        "permissions": ["auth.self.read"],
        "responses": {
            200: "Información del usuario autenticado obtenida correctamente.",
            401: "Token ausente, inválido o expirado.",
            404: "El usuario autenticado no existe.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.invalid_token",
            "auth.expired_token",
            "user.not_found",
        ],
        "service_docstring": "Resuelve usuario autenticado y retorna perfil seguro.",
    },
    "users_create": {
        "summary": "Crear usuario interno",
        "description": "Crea una cuenta interna para operación administrativa o de campo.",
        "permissions": ["user.create"],
        "responses": {
            201: "Usuario creado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos para crear usuarios.",
            409: "El correo ya existe.",
            422: "La solicitud contiene datos inválidos o incompletos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "user.email_already_exists",
            "user.role_invalid",
            "common.validation_error",
        ],
        "service_docstring": "Crea usuario interno validando rol y correo único.",
    },
    "users_list": {
        "summary": "Listar usuarios internos",
        "description": "Lista cuentas internas para administracion y control de acceso.",
        "permissions": ["user.read"],
        "responses": {
            200: "Listado de usuarios obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden"],
        "service_docstring": "Lista usuarios excluyendo datos sensibles.",
    },
    "users_get": {
        "summary": "Consultar usuario interno",
        "description": "Retorna el detalle de un usuario interno especifico.",
        "permissions": ["user.read"],
        "responses": {
            200: "Usuario obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Usuario no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "user.not_found"],
        "service_docstring": "Obtiene usuario por identificador.",
    },
    "users_update": {
        "summary": "Actualizar usuario interno",
        "description": "Actualiza atributos editables de una cuenta interna.",
        "permissions": ["user.update"],
        "responses": {
            200: "Usuario actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Usuario no existe.",
            409: "Conflicto por reglas de negocio.",
            422: "La solicitud contiene datos inválidos o incompletos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "user.not_found",
            "user.email_already_exists",
            "user.role_invalid",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza usuario de forma parcial con validaciones.",
    },
    "users_delete": {
        "summary": "Desactivar usuario interno",
        "description": "Realiza desactivación lógica de la cuenta interna.",
        "permissions": ["user.delete"],
        "responses": {
            200: "Usuario desactivado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Usuario no existe.",
            409: "No se permite autoeliminacion.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "user.not_found",
            "user.self_delete_forbidden",
        ],
        "service_docstring": "Marca usuario como inactivo manteniendo trazabilidad.",
    },
    "experiences_create": {
        "summary": "Crear experiencia",
        "description": "Crea una experiencia del catálogo operativo.",
        "permissions": ["experience.create"],
        "responses": {
            201: "Experiencia creada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            409: "Slug duplicado.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "experience.slug_already_exists",
            "experience.invalid_duration",
            "experience.invalid_capacity",
            "common.validation_error",
        ],
        "service_docstring": "Crea experiencia de catálogo sin mezclar agenda operativa.",
    },
    "experiences_list": {
        "summary": "Listar experiencias",
        "description": "Lista experiencias del catálogo.",
        "permissions": ["experience.read"],
        "responses": {
            200: "Listado de experiencias obtenido correctamente.",
            401: "No autenticado.",
        },
        "error_codes": ["auth.unauthorized"],
        "service_docstring": "Lista catálogo de experiencias.",
    },
    "experiences_get": {
        "summary": "Consultar experiencia",
        "description": "Retorna detalle de una experiencia por identificador.",
        "permissions": ["experience.read"],
        "responses": {
            200: "Experiencia obtenida correctamente.",
            401: "No autenticado.",
            404: "Experiencia no existe.",
        },
        "error_codes": ["auth.unauthorized", "experience.not_found"],
        "service_docstring": "Obtiene una experiencia por id.",
    },
    "experiences_update": {
        "summary": "Actualizar experiencia",
        "description": "Actualiza una experiencia del catálogo.",
        "permissions": ["experience.update"],
        "responses": {
            200: "Experiencia actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Experiencia no existe.",
            409: "Slug duplicado.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "experience.not_found",
            "experience.slug_already_exists",
            "experience.invalid_duration",
            "experience.invalid_capacity",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza experiencia con validaciones de coherencia.",
    },
    "experiences_delete": {
        "summary": "Desactivar experiencia",
        "description": "Desactiva una experiencia del catálogo.",
        "permissions": ["experience.delete"],
        "responses": {
            200: "Experiencia desactivada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Experiencia no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "experience.not_found"],
        "service_docstring": "Realiza inactivación lógica de experiencia.",
    },
    "experiences_quote": {
        "summary": "Cotizar experiencia",
        "description": (
            "Calcula la cotización oficial para una experiencia según cantidad "
            "de participantes y tabla tarifaria vigente."
        ),
        "permissions": ["experience.read"],
        "responses": {
            200: "Cotización calculada correctamente.",
            400: "La experiencia no tiene tarifas configuradas.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Experiencia o schedule no existe.",
            409: "Conflicto de estado o tarifa no disponible.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "experience.not_found",
            "schedule.not_found",
            "experience.inactive",
            "experience.pricing_missing",
            "experience.pricing_tier_not_found",
            "schedule.experience_mismatch",
            "common.validation_error",
        ],
        "service_docstring": "Calcula cotización oficial basada en tarifas y participantes.",
    },
    "schedules_create": {
        "summary": "Crear fecha operativa",
        "description": "Crea una fecha operativa reservable de una experiencia.",
        "permissions": ["schedule.create"],
        "responses": {
            201: "Fecha operativa creada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Experiencia no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "experience.not_found",
            "schedule.invalid_capacity",
            "schedule.invalid_slot_values",
            "schedule.negative_availability",
            "schedule.invalid_status",
            "common.validation_error",
        ],
        "service_docstring": "Crea schedule validando capacidad y disponibilidad derivada.",
    },
    "schedules_list": {
        "summary": "Listar fechas operativas",
        "description": "Lista fechas operativas con filtros de estado y rango.",
        "permissions": ["schedule.read"],
        "responses": {
            200: "Listado de fechas operativas obtenido correctamente.",
            401: "No autenticado.",
        },
        "error_codes": ["auth.unauthorized"],
        "service_docstring": "Lista schedules con información de cupos.",
    },
    "schedules_get": {
        "summary": "Consultar fecha operativa",
        "description": "Retorna detalle de una fecha operativa.",
        "permissions": ["schedule.read"],
        "responses": {
            200: "Fecha operativa obtenida correctamente.",
            401: "No autenticado.",
            404: "Fecha operativa no existe.",
        },
        "error_codes": ["auth.unauthorized", "schedule.not_found"],
        "service_docstring": "Obtiene schedule por id.",
    },
    "schedules_update": {
        "summary": "Actualizar fecha operativa",
        "description": "Actualiza capacidad, bloqueos o estado de una fecha operativa.",
        "permissions": ["schedule.update"],
        "responses": {
            200: "Fecha operativa actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Fecha operativa no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "schedule.not_found",
            "schedule.invalid_capacity",
            "schedule.invalid_slot_values",
            "schedule.negative_availability",
            "schedule.invalid_status",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza schedule recalculando disponibilidad.",
    },
    "schedules_delete": {
        "summary": "Desactivar fecha operativa",
        "description": "Desactiva una fecha operativa preservando historial.",
        "permissions": ["schedule.delete"],
        "responses": {
            200: "Fecha operativa desactivada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Fecha operativa no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "schedule.not_found"],
        "service_docstring": "Realiza inactivación lógica de schedule.",
    },
    "reservations_create": {
        "summary": "Crear reserva",
        "description": "Crea una reserva en estado inicial del flujo principal.",
        "permissions": ["reservation.create"],
        "responses": {
            201: "Reserva creada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Experiencia o fecha operativa no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "experience.not_found",
            "schedule.not_found",
            "reservation.invalid_participant_count",
            "reservation.schedule_mismatch",
            "common.validation_error",
        ],
        "service_docstring": "Crea reserva sin confirmarla ni descontar cupos.",
    },
    "reservations_availability": {
        "summary": "Consultar disponibilidad de reserva",
        "description": (
            "Consulta si una fecha está libre contra las reservas activas reales. "
            "La disponibilidad se decide por la colección de reservas activas."
        ),
        "permissions": ["reservation.read"],
        "responses": {
            200: "Disponibilidad obtenida correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            422: "Datos inválidos.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "common.validation_error"],
        "service_docstring": "Consulta disponibilidad real por fecha contra reservas activas.",
    },
    "reservations_list": {
        "summary": "Listar reservas",
        "description": "Lista reservas segun alcance del rol y filtros operativos.",
        "permissions": ["reservation.read"],
        "responses": {
            200: "Listado de reservas obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden"],
        "service_docstring": "Lista reservas con restricciones de visibilidad por rol.",
    },
    "reservations_get": {
        "summary": "Consultar reserva",
        "description": "Retorna detalle consolidado de una reserva.",
        "permissions": ["reservation.read"],
        "responses": {
            200: "Reserva obtenida correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "reservation.not_found"],
        "service_docstring": "Obtiene reserva por id con control de acceso.",
    },
    "reservations_update": {
        "summary": "Actualizar reserva",
        "description": "Actualiza atributos editables respetando reglas del estado actual.",
        "permissions": ["reservation.update"],
        "responses": {
            200: "Reserva actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
            409: "Conflicto de estado.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "reservation.invalid_status_transition",
            "reservation.already_cancelled",
            "reservation.already_completed",
            "reservation.invalid_participant_count",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza reserva sin ejecutar confirmación/cancelacion implicita.",
    },
    "reservations_transition": {
        "summary": "Transicionar estado de reserva",
        "description": "Ejecuta una transición de estado controlada por máquina de estados.",
        "permissions": ["reservation.update"],
        "responses": {
            200: "Estado de reserva actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
            409: "Conflicto de estado.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "reservation.invalid_status_transition",
            "common.validation_error",
        ],
        "service_docstring": "Transiciona estado de reserva validando flujo permitido.",
    },
    "reservations_confirm": {
        "summary": "Confirmar reserva",
        "description": "Confirma una reserva aplicando validaciones críticas de negocio.",
        "permissions": ["reservation.confirm"],
        "responses": {
            200: "Reserva confirmada correctamente.",
            400: "Reglas de negocio incumplidas.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva o schedule no existe.",
            409: "Conflicto de estado o disponibilidad.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "schedule.not_found",
            "reservation.invalid_status_transition",
            "reservation.confirmation_not_allowed",
            "reservation.min_notice_violation",
            "reservation.no_availability",
            "reservation.payment_required",
            "reservation.payment_not_verified",
            "schedule.not_open",
            "schedule.already_full",
            "participant.operationally_incomplete",
        ],
        "service_docstring": "Confirma reserva validando anticipación, pago y cupos.",
    },
    "reservations_cancel": {
        "summary": "Cancelar reserva",
        "description": "Cancela reserva respetando transiciones válidas y reversando cupos cuando aplica.",
        "permissions": ["reservation.cancel"],
        "responses": {
            200: "Reserva cancelada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
            409: "No puede cancelarse en estado actual.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "reservation.cancellation_not_allowed",
            "reservation.already_cancelled",
            "reservation.already_completed",
        ],
        "service_docstring": "Cancela reserva y revierte impacto operativo.",
    },
    "reservation_payment_proofs_create": {
        "summary": "Adjuntar comprobante de pago",
        "description": "Asocia metadatos de comprobante a una reserva con referencia externa.",
        "permissions": ["payment_proof.create"],
        "responses": {
            201: "Comprobante asociado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "payment_proof.storage_key_required",
            "payment_proof.invalid_content_type",
            "payment_proof.invalid_size",
            "payment_proof.hash_required",
            "common.validation_error",
        ],
        "service_docstring": "Registra metadatos y storage_key del comprobante.",
    },
    "payment_proofs_get": {
        "summary": "Consultar comprobante de pago",
        "description": "Retorna metadatos de un comprobante de pago.",
        "permissions": ["payment_proof.read"],
        "responses": {
            200: "Comprobante obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Comprobante no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "payment_proof.not_found"],
        "service_docstring": "Obtiene comprobante por id sin exponer binario.",
    },
    "payment_proofs_download": {
        "summary": "Descargar archivo de comprobante de pago",
        "description": "Descarga el archivo binario (imagen o PDF) del comprobante de pago. Si el archivo aun no se ha descargado de WhatsApp, retorna 202 Accepted.",
        "permissions": ["payment_proof.read"],
        "responses": {
            200: "Archivo binario del comprobante.",
            202: "Archivo pendiente de descarga desde WhatsApp.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Comprobante o archivo no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "payment_proof.not_found", "payment_proof.file_not_found"],
        "service_docstring": "Descarga el archivo binario de un comprobante de pago desde S3/local.",
    },
    "payment_proofs_update": {
        "summary": "Actualizar comprobante de pago",
        "description": "Actualiza estado o metadatos de validacion de comprobante.",
        "permissions": ["payment.verify"],
        "responses": {
            200: "Comprobante actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Comprobante o reserva no existe.",
            409: "Inconsistencia entre comprobante y reserva.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "payment_proof.not_found",
            "reservation.not_found",
            "payment_proof.reservation_mismatch",
        ],
        "service_docstring": "Actualiza estado de comprobante para revision administrativa.",
    },
    "participants_create": {
        "summary": "Registrar participante",
        "description": "Registra participante vinculado a una reserva.",
        "permissions": ["participant.create"],
        "responses": {
            201: "Participante registrado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
            400: "Reglas operativas incumplidas.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "participant.invalid_birth_date",
            "participant.invalid_weight",
            "participant.invalid_height",
            "participant.data_processing_required",
            "participant.missing_required_fields",
            "participant.operationally_incomplete",
            "common.validation_error",
        ],
        "service_docstring": "Crea participante y calcula completitud operativa.",
    },
    "participants_get": {
        "summary": "Consultar participante",
        "description": "Retorna detalle de un participante.",
        "permissions": ["participant.read"],
        "responses": {
            200: "Participante obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Participante no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "participant.not_found"],
        "service_docstring": "Obtiene participante por id.",
    },
	"participants_update": {
        "summary": "Actualizar participante",
        "description": "Actualiza participante y recalcula completitud.",
        "permissions": ["participant.update"],
        "responses": {
            200: "Participante actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Participante no existe.",
            400: "Reglas operativas incumplidas.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "participant.not_found",
            "participant.invalid_birth_date",
            "participant.invalid_weight",
            "participant.invalid_height",
            "participant.data_processing_required",
            "participant.missing_required_fields",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza datos operativos de participante.",
    },
    "equines_create": {
        "summary": "Crear equino",
        "description": "Registra un equino para operación.",
        "permissions": ["equine.create"],
        "responses": {
            201: "Equino creado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "equine.invalid_weight",
            "common.validation_error",
        ],
        "service_docstring": "Crea registro base de equino.",
    },
    "equines_list": {
        "summary": "Listar equinos",
        "description": "Lista equinos y su disponibilidad operativa.",
        "permissions": ["equine.read"],
        "responses": {200: "Listado de equinos obtenido correctamente.", 401: "No autenticado."},
        "error_codes": ["auth.unauthorized"],
        "service_docstring": "Lista equinos registrados.",
    },
    "equines_get": {
        "summary": "Consultar equino",
        "description": "Retorna detalle de un equino.",
        "permissions": ["equine.read"],
        "responses": {
            200: "Equino obtenido correctamente.",
            401: "No autenticado.",
            404: "Equino no existe.",
        },
        "error_codes": ["auth.unauthorized", "equine.not_found"],
        "service_docstring": "Obtiene equino por id.",
    },
    "equines_update": {
        "summary": "Actualizar equino",
        "description": "Actualiza atributos base de un equino.",
        "permissions": ["equine.update"],
        "responses": {
            200: "Equino actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Equino no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "equine.not_found",
            "equine.invalid_weight",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza equino y su disponibilidad.",
    },
    "equines_delete": {
        "summary": "Desactivar equino",
        "description": "Desactiva o marca no disponible un equino.",
        "permissions": ["equine.update"],
        "responses": {
            200: "Equino desactivado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Equino no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "equine.not_found"],
        "service_docstring": "Realiza inactivación lógica de equino.",
    },
    "equines_timeline": {
        "summary": "Timeline del equino",
        "description": "Retorna el historial cronológico del equino basado en ServiceLogs.",
        "permissions": ["equine.read"],
        "responses": {
            200: "Timeline obtenido correctamente.",
            401: "No autenticado.",
            404: "Equino no encontrado.",
        },
        "error_codes": ["auth.unauthorized", "equine.not_found"],
        "service_docstring": "Obtiene timeline de un equino desde ServiceLogs.",
    },
    "equines_available_for_reservation": {
        "summary": "Equinos disponibles para reserva",
        "description": "Retorna equinos activos y disponibles no asignados a la reserva.",
        "permissions": ["equine.read"],
        "responses": {
            200: "Listado de equinos disponibles obtenido correctamente.",
            401: "No autenticado.",
        },
        "error_codes": ["auth.unauthorized"],
        "service_docstring": "Lista equinos disponibles para una reserva.",
    },
    "saddles_create": {
        "summary": "Crear silla",
        "description": "Registra una silla operativa.",
        "permissions": ["saddle.create"],
        "responses": {
            201: "Silla creada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            409: "Código duplicado.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "saddle.code_already_exists",
            "common.validation_error",
        ],
        "service_docstring": "Crea silla validando código único.",
    },
    "saddles_list": {
        "summary": "Listar sillas",
        "description": "Lista sillas operativas registradas.",
        "permissions": ["saddle.read"],
        "responses": {200: "Listado de sillas obtenido correctamente.", 401: "No autenticado."},
        "error_codes": ["auth.unauthorized"],
        "service_docstring": "Lista sillas registradas.",
    },
    "saddles_get": {
        "summary": "Consultar silla",
        "description": "Retorna detalle de una silla operativa.",
        "permissions": ["saddle.read"],
        "responses": {
            200: "Silla obtenida correctamente.",
            401: "No autenticado.",
            404: "Silla no existe.",
        },
        "error_codes": ["auth.unauthorized", "saddle.not_found"],
        "service_docstring": "Obtiene silla por id.",
    },
    "saddles_delete": {
        "summary": "Eliminar silla",
        "description": "Borra lógicamente una silla estableciendo deleted_at.",
        "permissions": ["saddle.delete"],
        "responses": {
            200: "Silla eliminada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Silla no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "saddle.not_found"],
        "service_docstring": "Borra lógicamente una silla.",
    },
    "saddles_update": {
        "summary": "Actualizar silla",
        "description": "Actualiza atributos de una silla operativa.",
        "permissions": ["saddle.update"],
        "responses": {
            200: "Silla actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Silla no existe.",
            409: "Código duplicado.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "saddle.not_found",
            "saddle.code_already_exists",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza silla validando unicidad de código.",
    },
    "assignments_create": {
        "summary": "Registrar asignacion operativa",
        "description": "Registra asignacion de participante, equino y silla.",
        "permissions": ["assignment.create"],
        "responses": {
            201: "Asignacion registrada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Recurso relacionado no existe.",
            409: "Conflicto por recurso asignado o no disponible.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "participant.not_found",
            "equine.not_found",
            "saddle.not_found",
            "assignment.participant_not_in_reservation",
            "assignment.equine_already_assigned",
            "assignment.saddle_already_assigned",
            "assignment.invalid_priority",
            "equine.unavailable",
            "saddle.unavailable",
            "common.validation_error",
        ],
        "service_docstring": "Registra asignacion operativa con validaciones de seguridad.",
    },
    "assignments_get": {
        "summary": "Consultar asignacion",
        "description": "Retorna detalle de una asignacion operativa.",
        "permissions": ["assignment.read"],
        "responses": {
            200: "Asignacion obtenida correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Asignacion no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "assignment.not_found"],
        "service_docstring": "Obtiene asignacion por id.",
    },
    "assignments_update": {
        "summary": "Actualizar asignacion operativa",
        "description": "Actualiza una asignacion existente con revalidacion de recursos.",
        "permissions": ["assignment.update"],
        "responses": {
            200: "Asignacion actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Asignacion o recurso no existe.",
            409: "Conflicto por recurso asignado o no disponible.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "assignment.not_found",
            "equine.not_found",
            "saddle.not_found",
            "assignment.equine_already_assigned",
            "assignment.saddle_already_assigned",
            "equine.unavailable",
            "saddle.unavailable",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza asignacion validando coherencia operativa.",
    },
    "logs_create": {
        "summary": "Registrar evento de bitácora",
        "description": "Registra un hito operativo de una salida.",
        "permissions": ["log.create"],
        "responses": {
            201: "Evento registrado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no existe.",
            400: "Regla de evento incumplida.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "log.invalid_event_type",
            "log.checkpoint_name_required",
            "common.validation_error",
        ],
        "service_docstring": "Registra evento de bitácora validando campos dependientes.",
    },
    "logs_get": {
        "summary": "Consultar evento de bitácora",
        "description": "Retorna detalle de un evento de bitácora.",
        "permissions": ["log.read"],
        "responses": {
            200: "Evento obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Evento no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "log.not_found"],
        "service_docstring": "Obtiene evento de bitácora por id.",
    },
    "logs_update": {
        "summary": "Actualizar evento de bitácora",
        "description": "Actualiza un evento de bitácora existente.",
        "permissions": ["log.update"],
        "responses": {
            200: "Evento actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Evento no existe.",
            400: "Regla de evento incumplida.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "log.not_found",
            "log.invalid_event_type",
            "log.checkpoint_name_required",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza bitácora revalidando tipo de evento.",
    },
    "providers_create": {
        "summary": "Crear proveedor",
        "description": "Registra un proveedor operativo o comercial.",
        "permissions": ["provider.create"],
        "responses": {
            201: "Proveedor creado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            422: "Datos inválidos.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "common.validation_error"],
        "service_docstring": "Crea proveedor para operación.",
    },
    "providers_get": {
        "summary": "Consultar proveedor",
        "description": "Retorna detalle de un proveedor.",
        "permissions": ["provider.read"],
        "responses": {
            200: "Proveedor obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Proveedor no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "provider.not_found"],
        "service_docstring": "Obtiene proveedor por id.",
    },
    "providers_update": {
        "summary": "Actualizar proveedor",
        "description": "Actualiza datos de un proveedor.",
        "permissions": ["provider.update"],
        "responses": {
            200: "Proveedor actualizado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Proveedor no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "provider.not_found",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza proveedor de forma parcial.",
    },
    "providers_delete": {
        "summary": "Desactivar proveedor",
        "description": "Desactiva proveedor conservando trazabilidad.",
        "permissions": ["provider.delete"],
        "responses": {
            200: "Proveedor desactivado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Proveedor no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "provider.not_found"],
        "service_docstring": "Elimina lógicamente proveedor.",
    },
    "policies_create": {
        "summary": "Registrar póliza",
        "description": "Registra póliza asociada a reserva y proveedor opcional.",
        "permissions": ["policy.create"],
        "responses": {
            201: "Póliza registrada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva o proveedor no existe.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "provider.not_found",
            "common.validation_error",
        ],
        "service_docstring": "Crea póliza ligada a reserva.",
    },
    "policies_get": {
        "summary": "Consultar póliza",
        "description": "Retorna detalle de una póliza.",
        "permissions": ["policy.read"],
        "responses": {
            200: "Póliza obtenida correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Póliza no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "policy.not_found"],
        "service_docstring": "Obtiene póliza por id.",
    },
    "policies_update": {
        "summary": "Actualizar póliza",
        "description": "Actualiza atributos editables de una póliza.",
        "permissions": ["policy.update"],
        "responses": {
            200: "Póliza actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Póliza no existe.",
            409: "Inconsistencia de reserva.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "policy.not_found",
            "policy.reservation_mismatch",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza póliza manteniendo coherencia con reserva.",
    },
    "config_get": {
        "summary": "Consultar reglas de reserva",
        "description": "Retorna configuración activa que afecta confirmación de reservas.",
        "permissions": ["config.read"],
        "responses": {
            200: "Configuración obtenida correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Configuración no existe.",
        },
        "error_codes": ["auth.unauthorized", "auth.forbidden", "config.not_found"],
        "service_docstring": "Obtiene bloque de reglas de reserva.",
    },
    "config_emergency_contacts": {
        "summary": "Obtener contactos de emergencia",
        "description": (
            "Retorna el catálogo nacional de números de emergencia disponibles en Colombia. "
            "Este endpoint proporciona información estandarizada para interfaces móviles y "
            "flujos operativos, permitiendo acceso rápido a líneas críticas de seguridad, "
            "salud y asistencia social. El catálogo es estable, de baja frecuencia de cambio "
            "y puede ser cacheado por el cliente."
        ),
        "permissions": [],
        "responses": {200: "Listado de contactos de emergencia obtenido correctamente."},
        "error_codes": [],
        "service_docstring": (
            "Retorna el catálogo de números de emergencia nacionales de forma estable y cacheable."
        ),
    },
    "config_update": {
        "summary": "Actualizar reglas de reserva",
        "description": "Actualiza parámetros sensibles de confirmación de reservas.",
        "permissions": ["config.update"],
        "responses": {
            200: "Configuración actualizada correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Configuración no existe.",
            400: "Regla de negocio inválida.",
            422: "Datos inválidos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "config.not_found",
            "config.invalid_min_days",
            "common.validation_error",
        ],
        "service_docstring": "Actualiza configuración validando min_days_in_advance.",
    },
    "participant_form_validate_token": {
        "summary": "Validar token del formulario",
        "description": "Valida que un token de formulario sea válido, no haya expirado y tenga cupos disponibles.",
        "permissions": [],
        "responses": {
            200: "Resultado de validación del token.",
        },
        "error_codes": [],
        "service_docstring": "Valida token de formulario de participantes.",
    },
    "participant_form_public_status": {
        "summary": "Estado público del formulario",
        "description": "Retorna estado agregado del formulario: completados, esperados, sin datos sensibles.",
        "permissions": [],
        "responses": {
            200: "Estado agregado del formulario.",
            404: "Token inválido o reserva no encontrada.",
        },
        "error_codes": ["form_link.invalid_token", "reservation.not_found"],
        "service_docstring": "Retorna estado agregado público del formulario.",
    },
    "participant_form_public_create": {
        "summary": "Registrar participante desde formulario público",
        "description": "Crea un participante asociado a la reserva mediante un token válido del formulario.",
        "permissions": [],
        "responses": {
            201: "Participante registrado correctamente.",
            400: "Fecha de nacimiento inválida.",
            404: "Token inválido.",
            409: "Enlace expirado, revocado o cupo máximo alcanzado.",
            410: "Enlace expirado o revocado.",
            422: "Datos inválidos o falta aceptar tratamiento de datos/liberación.",
        },
        "error_codes": [
            "form_link.invalid_token",
            "form_link.expired",
            "form_link.revoked",
            "form_link.max_participants_reached",
            "form_link.already_completed",
            "participant.invalid_birth_date",
            "participant.data_processing_required",
            "participant.risk_release_required",
            "common.validation_error",
        ],
        "service_docstring": "Crea participante desde formulario público con validaciones de token.",
    },
    "participant_form_risk_release_text": {
        "summary": "Obtener texto de liberación de responsabilidad",
        "description": "Retorna el texto vigente de liberación de responsabilidad y asunción de riesgos.",
        "permissions": [],
        "responses": {
            200: "Texto de liberación de responsabilidad.",
        },
        "error_codes": [],
        "service_docstring": "Retorna el texto de liberación de responsabilidad.",
    },
    "participant_form_generate_link": {
        "summary": "Generar enlace de formulario",
        "description": "Genera un enlace temporal para que los participantes de una reserva confirmada diligencien sus datos.",
        "permissions": ["participant_form_link.create"],
        "responses": {
            201: "Enlace generado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "Reserva no encontrada.",
            409: "La reserva no está confirmada.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "reservation.not_found",
            "form_link.reservation_not_confirmed",
        ],
        "service_docstring": "Genera enlace temporal de formulario de participantes.",
    },
    "participant_form_revoke_link": {
        "summary": "Revocar enlace de formulario",
        "description": "Revoca manualmente un enlace de formulario activo.",
        "permissions": ["participant_form_link.revoke"],
        "responses": {
            200: "Enlace revocado correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
            404: "No hay enlace activo para esta reserva.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
            "form_link.not_found",
        ],
        "service_docstring": "Revoca enlace de formulario de participantes.",
    },
    "participant_form_get_link": {
        "summary": "Consultar enlace de formulario",
        "description": "Retorna el estado del enlace de formulario activo o el último generado.",
        "permissions": ["participant_form_link.read"],
        "responses": {
            200: "Estado del enlace obtenido correctamente.",
            401: "No autenticado.",
            403: "Sin permisos.",
        },
        "error_codes": [
            "auth.unauthorized",
            "auth.forbidden",
        ],
        "service_docstring": "Obtiene estado del enlace de formulario.",
    },
}


ENDPOINT_ROUTE_MAP: dict[str, tuple[str, str]] = {
    "auth_register": ("POST", "/api/v1/auth/register"),
    "auth_login": ("POST", "/api/v1/auth/login"),
    "auth_refresh": ("POST", "/api/v1/auth/refresh"),
    "auth_logout": ("POST", "/api/v1/auth/logout"),
    "auth_change_password": ("POST", "/api/v1/auth/change-password"),
    "auth_me": ("GET", "/api/v1/auth/me"),
    "users_create": ("POST", "/api/v1/users"),
    "users_list": ("GET", "/api/v1/users"),
    "users_get": ("GET", "/api/v1/users/{user_id}"),
    "users_update": ("PATCH", "/api/v1/users/{user_id}"),
    "users_delete": ("DELETE", "/api/v1/users/{user_id}"),
    "experiences_create": ("POST", "/api/v1/experiences"),
    "experiences_list": ("GET", "/api/v1/experiences"),
    "experiences_get": ("GET", "/api/v1/experiences/{experience_id}"),
    "experiences_update": ("PATCH", "/api/v1/experiences/{experience_id}"),
    "experiences_delete": ("DELETE", "/api/v1/experiences/{experience_id}"),
    "experiences_quote": ("POST", "/api/v1/experiences/{experience_id}/quote"),
    "schedules_create": ("POST", "/api/v1/schedules"),
    "schedules_list": ("GET", "/api/v1/schedules"),
    "schedules_get": ("GET", "/api/v1/schedules/{schedule_id}"),
    "schedules_update": ("PATCH", "/api/v1/schedules/{schedule_id}"),
    "schedules_delete": ("DELETE", "/api/v1/schedules/{schedule_id}"),
    "reservations_create": ("POST", "/api/v1/reservations"),
    "reservations_availability": ("GET", "/api/v1/reservations/availability"),
    "reservations_list": ("GET", "/api/v1/reservations"),
    "reservations_get": ("GET", "/api/v1/reservations/{reservation_id}"),
    "reservations_update": ("PATCH", "/api/v1/reservations/{reservation_id}"),
    "reservations_transition": ("POST", "/api/v1/reservations/{reservation_id}/status"),
    "reservations_confirm": ("POST", "/api/v1/reservations/{reservation_id}/confirm"),
    "reservations_cancel": ("POST", "/api/v1/reservations/{reservation_id}/cancel"),
    "reservation_payment_proofs_create": (
        "POST",
        "/api/v1/reservations/{reservation_id}/payment-proofs",
    ),
    "participants_create": ("POST", "/api/v1/reservations/{reservation_id}/participants"),
    "payment_proofs_get": ("GET", "/api/v1/payment-proofs/{payment_proof_id}"),
    "payment_proofs_download": ("GET", "/api/v1/payment-proofs/{payment_proof_id}/download"),
    "payment_proofs_update": ("PATCH", "/api/v1/payment-proofs/{payment_proof_id}"),
    "participants_get": ("GET", "/api/v1/participants/{participant_id}"),
    "participants_update": ("PATCH", "/api/v1/participants/{participant_id}"),
    "equines_create": ("POST", "/api/v1/equines"),
    "equines_list": ("GET", "/api/v1/equines"),
    "equines_get": ("GET", "/api/v1/equines/{equine_id}"),
    "equines_update": ("PATCH", "/api/v1/equines/{equine_id}"),
    "equines_delete": ("DELETE", "/api/v1/equines/{equine_id}"),
    "equines_timeline": ("GET", "/api/v1/equines/{equine_id}/timeline"),
    "equines_available_for_reservation": (
        "GET",
        "/api/v1/equines/available-for-reservation/{reservation_id}",
    ),
    "saddles_create": ("POST", "/api/v1/saddles"),
    "saddles_list": ("GET", "/api/v1/saddles"),
    "saddles_get": ("GET", "/api/v1/saddles/{saddle_id}"),
    "saddles_update": ("PATCH", "/api/v1/saddles/{saddle_id}"),
    "saddles_delete": ("DELETE", "/api/v1/saddles/{saddle_id}"),
    "assignments_create": ("POST", "/api/v1/assignments"),
    "assignments_get": ("GET", "/api/v1/assignments/{assignment_id}"),
    "assignments_update": ("PATCH", "/api/v1/assignments/{assignment_id}"),
    "logs_create": ("POST", "/api/v1/logs"),
    "logs_get": ("GET", "/api/v1/logs/{log_id}"),
    "logs_update": ("PATCH", "/api/v1/logs/{log_id}"),
    "providers_create": ("POST", "/api/v1/providers"),
    "providers_get": ("GET", "/api/v1/providers/{provider_id}"),
    "providers_update": ("PATCH", "/api/v1/providers/{provider_id}"),
    "providers_delete": ("DELETE", "/api/v1/providers/{provider_id}"),
    "policies_create": ("POST", "/api/v1/policies"),
    "policies_get": ("GET", "/api/v1/policies/{policy_id}"),
    "policies_update": ("PATCH", "/api/v1/policies/{policy_id}"),
    "config_emergency_contacts": ("GET", "/api/v1/config/emergency-contacts"),
    "config_get": ("GET", "/api/v1/config/reservation-rules"),
    "config_update": ("PATCH", "/api/v1/config/reservation-rules"),
    "participant_form_validate_token": (
        "GET",
        "/api/v1/public/participant-forms/{token}/validate",
    ),
    "participant_form_public_status": (
        "GET",
        "/api/v1/public/participant-forms/{token}/status",
    ),
    "participant_form_public_create": (
        "POST",
        "/api/v1/public/participant-forms/{token}/participants",
    ),
    "participant_form_risk_release_text": (
        "GET",
        "/api/v1/public/participant-forms/risk-release-text",
    ),
    "participant_form_generate_link": (
        "POST",
        "/api/v1/reservations/{reservation_id}/participant-form-link",
    ),
    "participant_form_revoke_link": (
        "POST",
        "/api/v1/reservations/{reservation_id}/participant-form-link/revoke",
    ),
    "participant_form_get_link": (
        "GET",
        "/api/v1/reservations/{reservation_id}/participant-form-link",
    ),
}

for endpoint_key, route in ENDPOINT_ROUTE_MAP.items():
    doc = ENDPOINT_DOCS[endpoint_key]
    matrix = ENDPOINT_BUSINESS_CASES.get(route)
    if matrix is None:
        continue
    case_ids = matrix["cases_400"] + matrix["cases_404"] + matrix["cases_409"]
    for case_id in case_ids:
        code = BUSINESS_ERROR_CASES[case_id]["code"]
        if code not in doc["error_codes"]:
            doc["error_codes"].append(code)


def endpoint_description(key: str) -> str:
    doc = ENDPOINT_DOCS[key]
    description = doc["description"]
    permissions = doc["permissions"] if doc["permissions"] else ["Público"]
    error_items = endpoint_error_items(key)
    business_case_names = endpoint_business_case_names(key)
    return (
        f"{description}\n\n"
        f"**Permisos requeridos**\n"
        f"{_as_markdown_list(permissions)}\n\n"
        f"**Errores esperados (número, código y mensaje)**\n"
        f"{_as_numbered_error_list(error_items)}\n\n"
        f"**Casos de uso aplicables**\n"
        f"{_as_markdown_list(business_case_names, empty='- Sin casos de negocio 400/404/409 declarados.')}"
    )


def endpoint_business_cases(key: str) -> tuple[str, ...]:
    route = ENDPOINT_ROUTE_MAP.get(key)
    if route is None:
        return ()
    mapped = ENDPOINT_BUSINESS_CASES.get(route)
    if mapped is None:
        return ()
    return mapped["cases_400"] + mapped["cases_404"] + mapped["cases_409"]


def endpoint_business_case_names(key: str) -> tuple[str, ...]:
    case_ids = endpoint_business_cases(key)
    names: list[str] = []
    for case_id in case_ids:
        names.append(BUSINESS_ERROR_CASES[case_id]["name"])
    return tuple(names)


def _as_markdown_list(items: list[str] | tuple[str, ...], empty: str = "- N/A") -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def _as_numbered_error_list(items: list[tuple[int | None, str, str]]) -> str:
    if not items:
        return "1. **Estado HTTP:** N/A<br>**Código:** `N/A`<br>**Mensaje:** No aplica."
    lines: list[str] = []
    for index, (http_status, code, message) in enumerate(items, start=1):
        status_text = str(http_status) if http_status is not None else "N/A"
        lines.append(
            f"{index}. **Estado HTTP:** {status_text}<br>"
            f"**Código:** `{code}`<br>"
            f"**Mensaje:** {message}"
        )
    return "\n\n".join(lines)


def _default_error_message(code: str) -> str:
    messages = {
        "common.validation_error": "La solicitud contiene datos inválidos o incompletos.",
        "auth.unauthorized": "No autenticado o token ausente.",
        "auth.invalid_token": "Token inválido.",
        "auth.expired_token": "Token expirado.",
        "auth.invalid_credentials": "Credenciales inválidas.",
        "auth.inactive_user": "Usuario inactivo.",
        "auth.forbidden": "No tiene permisos para esta acción.",
        "auth.password_mismatch": "La contraseña actual no coincide.",
        "common.internal_error": "Se presentó un error interno no controlado.",
        "common.conflict": "Existe un conflicto con el estado actual del recurso.",
        "common.resource_not_found": "El recurso solicitado no existe.",
    }
    return messages.get(code, "Error de negocio o validación del dominio.")


def _default_error_status(code: str) -> int | None:
    status_by_code = {
        "common.validation_error": 422,
        "auth.unauthorized": 401,
        "auth.invalid_token": 401,
        "auth.expired_token": 401,
        "auth.invalid_credentials": 401,
        "auth.inactive_user": 401,
        "auth.forbidden": 403,
        "auth.password_mismatch": 400,
        "common.resource_not_found": 404,
        "common.conflict": 409,
        "common.internal_error": 500,
    }
    return status_by_code.get(code)


def endpoint_error_items(key: str) -> list[tuple[int | None, str, str]]:
    doc = ENDPOINT_DOCS[key]
    route = ENDPOINT_ROUTE_MAP.get(key)
    case_ids: tuple[str, ...] = ()
    if route is not None and route in ENDPOINT_BUSINESS_CASES:
        matrix = ENDPOINT_BUSINESS_CASES[route]
        case_ids = matrix["cases_400"] + matrix["cases_404"] + matrix["cases_409"]

    business_info_by_code: dict[str, tuple[int, str]] = {}
    for case_id in case_ids:
        case = BUSINESS_ERROR_CASES[case_id]
        business_info_by_code[case["code"]] = (case["http_status"], case["name"])

    items: list[tuple[int | None, str, str]] = []
    seen: set[str] = set()
    for code in doc["error_codes"]:
        if code in seen:
            continue
        seen.add(code)
        if code in business_info_by_code:
            status, message = business_info_by_code[code]
        else:
            status = _default_error_status(code)
            message = _default_error_message(code)
        items.append((status, code, message))
    return items


def _detail_example_value(detail_key: str) -> object:
    examples: dict[str, object] = {
        "user_id": "660000000000000000000001",
        "provided_role": "superadmin",
        "duration_hours": None,
        "duration_days": None,
        "base_capacity": 0,
        "capacity_total": 0,
        "reserved_slots": -1,
        "blocked_slots": -1,
        "internal_slots": -1,
        "available_slots": 0,
        "status": "closed",
        "participant_count": 0,
        "reservation_experience_id": "660000000000000000000101",
        "schedule_experience_id": "660000000000000000000102",
        "required_days": 7,
        "service_date": "2026-04-24",
        "reservation_id": "660000000000000000000201",
        "payment_status": "pending",
        "reservation_status": "quoted",
        "content_type": "text/plain",
        "size_bytes": 0,
        "birth_date": "2030-01-01",
        "weight_kg": 0,
        "height_cm": 0,
        "participant_id": "660000000000000000000301",
        "missing_fields": ["document_number", "accepted_data_processing"],
        "priority": "urgent",
        "event_type": "unknown",
        "min_days_in_advance": -1,
        "experience_id": "660000000000000000000101",
        "schedule_id": "660000000000000000000401",
        "payment_proof_id": "660000000000000000000501",
        "equine_id": "660000000000000000000601",
        "saddle_id": "660000000000000000000701",
        "assignment_id": "660000000000000000000801",
        "log_id": "660000000000000000000901",
        "provider_id": "660000000000000000001001",
        "policy_id": "660000000000000000001101",
        "config_key": "reservation_rules",
        "email": "duplicado@lajuana.co",
        "slug": "cabalgata-basica",
        "current_status": "payment_received",
        "target_status": "contact",
        "required_slots": 3,
        "code": "S-001",
    }
    return examples.get(detail_key, "valor_no_disponible")


def _validation_error_example() -> dict[str, object]:
    return {
        "code": "common.validation_error",
        "message": "La solicitud contiene datos inválidos.",
        "details": {
            "fields": [
                {
                    "field": "email",
                    "reason": "El valor no tiene un formato válido.",
                }
            ]
        },
    }


def _error_examples_for_status(key: str, status_code: int) -> dict[str, dict[str, object]]:
    route = ENDPOINT_ROUTE_MAP.get(key)
    if route is None:
        return {}
    matrix = ENDPOINT_BUSINESS_CASES.get(route)
    if matrix is None:
        return {}

    case_ids: tuple[str, ...]
    if status_code == 400:
        case_ids = matrix["cases_400"]
    elif status_code == 404:
        case_ids = matrix["cases_404"]
    elif status_code == 409:
        case_ids = matrix["cases_409"]
    else:
        return {}

    examples: dict[str, dict[str, object]] = {}
    for case_id in case_ids:
        case = BUSINESS_ERROR_CASES[case_id]
        details = {
            detail_key: _detail_example_value(detail_key) for detail_key in case["detail_keys"]
        }
        examples[case_id] = {
            "summary": case["name"],
            "value": {
                "code": case["code"],
                "message": case["name"],
                "details": details if details else None,
            },
        }
    return examples


def endpoint_responses(key: str) -> dict[int, dict]:
    doc = ENDPOINT_DOCS[key]
    merged_responses = dict(doc["responses"])
    route = ENDPOINT_ROUTE_MAP.get(key)
    if route is not None and route in ENDPOINT_BUSINESS_CASES:
        matrix = ENDPOINT_BUSINESS_CASES[route]
        status_cases = {
            400: matrix["cases_400"],
            404: matrix["cases_404"],
            409: matrix["cases_409"],
        }
        default_text = {
            400: "La solicitud incumple reglas de negocio.",
            404: "El recurso solicitado no existe.",
            409: "Existe un conflicto con el estado actual del recurso.",
        }
        for status_code, case_ids in status_cases.items():
            if case_ids and status_code not in merged_responses:
                merged_responses[status_code] = default_text[status_code]

    responses: dict[int, dict] = {}
    for code, text in merged_responses.items():
        display_text = text
        item: dict = {"description": display_text}
        if code >= 400:
            item["model"] = ApiErrorResponse
            if code == 422:
                item["content"] = {"application/json": {"example": _validation_error_example()}}
                responses[code] = item
                continue
            case_examples = _error_examples_for_status(key, code)
            if case_examples:
                item["content"] = {"application/json": {"examples": case_examples}}
                responses[code] = item
                continue
            fallback_code = doc["error_codes"][0] if doc["error_codes"] else "common.error"
            example_body = {"code": fallback_code, "message": display_text, "details": None}
            item["content"] = {"application/json": {"example": example_body}}
        else:
            item["content"] = {"application/json": {"example": {"mensaje": display_text}}}
        responses[code] = item
    return responses
