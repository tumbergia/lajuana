"""Registro del change feed de sincronización.

Cada mutación de una entidad sincronizable debe dejar un ``SyncChangeDocument``
para que ``/sync/pull`` pueda entregarlo a los clientes (propagación entre
dispositivos). Este módulo centraliza:

* el mapeo ``entity_type`` → ``stream``,
* la construcción del ``payload`` (reutiliza los mismos mappers que el bootstrap
  y el push, para que el cliente reciba el formato que ya sabe aplicar),
* la inserción del documento de cambio.

El registro es *best-effort*: si falla, se loguea pero **no** rompe la mutación
de negocio que lo originó.
"""

import logging

from app.documents import AppConfigDocument, SyncChangeDocument
from app.documents.base import utc_now
from app.services.mappers import (
    assignment_to_response,
    equine_to_response,
    experience_to_response,
    participant_to_response,
    payment_proof_to_response,
    policy_to_response,
    provider_to_response,
    reservation_to_response,
    saddle_to_response,
    service_log_to_response,
)

logger = logging.getLogger(__name__)


# entity_type → nombre de stream usado por el cursor de pull
STREAM_BY_ENTITY: dict[str, str] = {
    "experience": "experiences",
    "reservation": "reservations",
    "participant": "participants",
    "payment_proof": "payment_proofs",
    "assignment": "assignments",
    "service_log": "logs",
    "provider": "providers",
    "policy": "policies",
    "saddle": "saddles",
    "equine": "equines",
    "reservation_rules": "config",
}


async def entity_to_response_dict(entity_type: str, doc) -> dict:
    """Convierte un documento de dominio al dict de respuesta JSON-safe.

    Reutilizado por ``SyncService`` para el payload de push/pull.
    """
    if entity_type == "experience":
        return experience_to_response(doc).model_dump(mode="json")
    if entity_type == "reservation_rules":
        if isinstance(doc, AppConfigDocument) and doc.reservation_rules is not None:
            return doc.reservation_rules.model_dump(mode="json")
        return {}
    if entity_type == "reservation":
        result = await reservation_to_response(doc)
        return result.model_dump(mode="json")
    if entity_type == "participant":
        return participant_to_response(doc).model_dump(mode="json")
    if entity_type == "payment_proof":
        return payment_proof_to_response(doc).model_dump(mode="json")
    if entity_type == "assignment":
        result = await assignment_to_response(doc)
        return result.model_dump(mode="json")
    if entity_type == "service_log":
        return service_log_to_response(doc).model_dump(mode="json")
    if entity_type == "provider":
        return provider_to_response(doc).model_dump(mode="json")
    if entity_type == "policy":
        return policy_to_response(doc).model_dump(mode="json")
    if entity_type == "saddle":
        return saddle_to_response(doc).model_dump(mode="json")
    if entity_type == "equine":
        return equine_to_response(doc).model_dump(mode="json")
    return doc.model_dump(mode="json")


async def _build_payload(entity_type: str, doc) -> dict:
    """Payload del cambio. ``config`` lleva una forma especial que el cliente
    (catalogs_repository._applyConfigChange) sabe interpretar."""
    if entity_type == "reservation_rules":
        rules = await entity_to_response_dict("reservation_rules", doc)
        return {
            "key": "reservation_rules",
            "reservation_rules": rules,
            "version": getattr(doc, "version", 1),
            "updated_at": getattr(doc, "updated_at", utc_now()).isoformat(),
        }
    return await entity_to_response_dict(entity_type, doc)


async def record_change(
    *,
    entity_type: str,
    doc,
    change_type: str = "upsert",
) -> None:
    """Inserta un ``SyncChangeDocument`` para *doc*. Best-effort."""
    stream = STREAM_BY_ENTITY.get(entity_type)
    if stream is None:
        return
    try:
        payload = await _build_payload(entity_type, doc)
        await SyncChangeDocument(
            stream=stream,
            entity_type=entity_type,
            entity_id=str(doc.id),
            change_type=change_type,
            version=getattr(doc, "version", 1),
            entity_updated_at=getattr(doc, "updated_at", utc_now()),
            payload=payload,
        ).insert()
    except Exception:  # pragma: no cover - el feed nunca debe romper la mutación
        logger.exception(
            "[sync] No se pudo registrar el cambio de %s/%s",
            entity_type,
            getattr(doc, "id", "?"),
        )
