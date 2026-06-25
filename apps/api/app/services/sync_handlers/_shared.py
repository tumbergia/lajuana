"""Shared utilities used by sync operation handlers."""

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import AppConfigDocument
from app.services.config_service import RESERVATION_RULES_KEY


async def ensure_base_version(
    document_class,
    entity_id: str | None,
    base_version: int | None,
) -> None:
    """Raise ``409 SYNC_STALE_VERSION`` if *entity_id* exists and its version
    differs from *base_version*."""
    if entity_id is None or base_version is None:
        return
    doc = await document_class.get(entity_id)
    if doc is None:
        return
    if base_version != doc.version:
        raise ApiError(
            status_code=409,
            code=ErrorCode.SYNC_STALE_VERSION,
            message="Entity version is outdated.",
            details={
                "entity_id": entity_id,
                "expected_version": doc.version,
                "received_version": base_version,
            },
        )


async def ensure_reservation_rules_base_version(base_version: int | None) -> None:
    """Raise ``409 SYNC_STALE_VERSION`` if reservation rules version differs."""
    if base_version is None:
        return
    config = await AppConfigDocument.find_one({"key": RESERVATION_RULES_KEY})
    if config is None:
        return
    if base_version != config.version:
        raise ApiError(
            status_code=409,
            code=ErrorCode.SYNC_STALE_VERSION,
            message="Entity version is outdated.",
            details={
                "entity_id": str(config.id),
                "expected_version": config.version,
                "received_version": base_version,
            },
        )


def require_remote_id(operation) -> None:
    """Raise ``400`` if ``operation.entity_remote_id`` is falsy."""
    if not operation.entity_remote_id:
        raise ApiError(
            status_code=400,
            code=ErrorCode.SYNC_UNSUPPORTED_OPERATION,
            message="entity_remote_id es obligatorio para esta operacion.",
        )


def strip_null_values(payload: dict) -> dict:
    """Remove keys whose value is ``None``.

    Sync clients often include optional fields as explicit JSON ``null`` values.
    Pydantic treats those as provided values and will not apply field defaults.
    """
    return {key: value for key, value in payload.items() if value is not None}


def require_field(payload: dict, key: str) -> str:
    """Raise ``400`` if *key* is missing or falsy in *payload*."""
    value = payload.get(key)
    if not value:
        raise ApiError(
            status_code=400,
            code=ErrorCode.VALIDATION_ERROR,
            message=f"El campo {key} es obligatorio.",
        )
    return str(value)
