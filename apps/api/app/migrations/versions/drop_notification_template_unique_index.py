"""Drop the legacy unique index on notification_templates.template_key.

Antes de poder tener templates bilingües (misma template_key en ES y EN),
se cambió el índice `template_key_1` de unique → non-unique en el documento.
Pero el índice viejo en MongoDB sigue siendo unique, lo que causa
IndexKeySpecsConflict al iniciar Beanie.

Este script:
  1. Busca el índice `template_key_1` en `notification_templates`.
  2. Si existe y es unique, lo elimina.
  3. Al reiniciar el API, Beanie creará el nuevo índice (non-unique)
     sin conflicto.
"""

import asyncio

from app.core.db import close_db, init_db
from app.documents.notification_template_document import NotificationTemplateDocument
from app.core.logging import logger


LEGACY_INDEX_NAME = "template_key_1"


async def drop_legacy_unique_index() -> bool:
    await init_db()
    collection = NotificationTemplateDocument.get_motor_collection()

    # Lee los índices actuales sincrónicamente
    indexes_info = await collection.index_information()
    legacy = indexes_info.get(LEGACY_INDEX_NAME)
    if legacy is None:
        logger.info("Legacy index %s not present, nothing to do", LEGACY_INDEX_NAME)
        return False

    if not legacy.get("unique", False):
        logger.info(
            "Index %s already non-unique, nothing to do", LEGACY_INDEX_NAME
        )
        return False

    logger.warning(
        "Dropping legacy unique index %s on notification_templates",
        LEGACY_INDEX_NAME,
    )
    await collection.drop_index(LEGACY_INDEX_NAME)
    return True


if __name__ == "__main__":
    try:
        dropped = asyncio.run(drop_legacy_unique_index())
        if dropped:
            print(
                f"OK: índice legacy '{LEGACY_INDEX_NAME}' (unique) eliminado. "
                "Reinicia el API para que Beanie cree el nuevo índice "
                "non-unique."
            )
        else:
            print(
                f"OK: nada que hacer. El índice '{LEGACY_INDEX_NAME}' "
                "ya está en estado correcto."
            )
    finally:
        asyncio.run(close_db())
