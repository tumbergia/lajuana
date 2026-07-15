"""Activa la IA del bot (ai_configuration.enabled = True).

El bot NO responde si ai_configuration.enabled = False en la collection
`app_config`. Por defecto está en False. Este script lo activa y deja
el resto de la config intacta (rutas, provider_mode, muted_phones).

Uso:
    uv run python -m app.migrations.versions.enable_bot_ai

Para desactivarlo de nuevo, el endpoint admin /api/v1/admin/config/ai
tiene el toggle.
"""

import asyncio

from app.core.db import close_db, init_db
from app.documents.app_config_document import AppConfigDocument
from app.core.logging import logger


AI_CONFIG_KEY = "ai_configuration"


async def enable_bot_ai() -> bool:
    await init_db()
    doc = await AppConfigDocument.find_one({"key": AI_CONFIG_KEY})
    if doc is None:
        logger.error(
            "No ai_configuration doc found. Run the seed migrations first."
        )
        return False

    ai_config = doc.ai_configuration
    if ai_config is None:
        logger.error("ai_configuration is None, cannot enable")
        return False

    if ai_config.enabled is True:
        logger.info("AI is already enabled, nothing to do")
        return False

    ai_config.enabled = True
    doc.ai_configuration = ai_config
    doc.version += 1
    await doc.save()
    logger.info(
        "AI enabled | version=%d | routes=%d",
        doc.version,
        len(ai_config.get("routes") or []),
    )
    return True


if __name__ == "__main__":
    try:
        enabled = asyncio.run(enable_bot_ai())
        if enabled:
            print(
                "OK: ai_configuration.enabled = True. "
                "Reinicia el API para que el cambio tome efecto."
            )
        else:
            print("OK: la IA ya estaba habilitada, nada que hacer.")
    finally:
        asyncio.run(close_db())
