import asyncio
import sys

from beanie import init_beanie
from openai import AsyncOpenAI
from pymongo import AsyncMongoClient, UpdateOne

from app.core.config import settings
from app.documents import (
    EquineDocument,
    ExperienceDocument,
    KnowledgeDocument,
    PolicyDocument,
)


async def generate_embedding(client: AsyncOpenAI, text: str) -> list[float]:
    response = await client.embeddings.create(
        model=settings.chat_embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def sync_knowledge() -> None:
    client = AsyncMongoClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]
    # --- PRUEBA DEFINITIVA ---
    print("=======================================")
    print(f"Me estoy conectando a la BD llamada: '{database.name}'")
    colecciones = await database.list_collection_names()
    print(f"Colecciones que veo aquí adentro: {colecciones}")
    print("=======================================")
    await init_beanie(
        database=database,
        document_models=[
            ExperienceDocument,
            EquineDocument,
            PolicyDocument,
            KnowledgeDocument,
        ],
    )

    embedding_client = AsyncOpenAI(
        api_key=settings.chat_embedding_api_key,
        base_url=settings.chat_embedding_base_url,
    )

    upsert_operations = []

    # 1. Experiencias
    experiences = await ExperienceDocument.find(ExperienceDocument.is_active == True).to_list()
    for exp in experiences:
        duration_text = ""
        duration = getattr(exp, "duration", None)
        if duration is not None:
            duration_text = getattr(duration, "display_text", None) or ""
            if not duration_text:
                activity_minutes = getattr(duration, "activity_minutes", None)
                route_minutes = getattr(duration, "route_minutes", None)
                if activity_minutes and route_minutes:
                    duration_text = f"{activity_minutes} min totales / {route_minutes} min de ruta"
        if not duration_text:
            duration_hours = getattr(exp, "duration_hours", None)
            duration_days = getattr(exp, "duration_days", None)
            if duration_hours is not None:
                duration_text = f"{duration_hours} horas"
            elif duration_days is not None:
                duration_text = f"{duration_days} días"

        level = getattr(exp, "level", None)
        level_text = getattr(level, "value", None) if hasattr(level, "value") else None
        if not level_text:
            level_text = str(level or "basic")

        text = (
            f"Experiencia: {exp.name}\n"
            f"Descripción: {getattr(exp, 'description', '')}\n"
            f"Nivel: {level_text}\n"
            f"Duración: {duration_text}"
        )
        source_ref = f"experience:{exp.id}"
        print(f"  - Generando embedding para experiencia: {exp.name}")
        embedding = await generate_embedding(embedding_client, text)

        upsert_operations.append(
            UpdateOne(
                {"source": source_ref},
                {
                    "$set": {
                        "type": "experience",
                        "title": exp.name,
                        "content": text,
                        "text": text,
                        "scope": "public",
                        "embedding": embedding,
                        "metadata": {"type": "experience", "id": str(exp.id), "title": exp.name},
                    }
                },
                upsert=True,
            )
        )

    # 2. Equinos
    equines = await EquineDocument.find_all().to_list()
    for equine in equines:
        availability_text = "Disponible." if equine.is_available else "No disponible."
        if getattr(equine, "availability_notes", None):
            availability_text += f" Notas: {equine.availability_notes}"

        text = (
            f"Equino: {equine.name}\n"
            f"Raza: {getattr(equine, 'breed', None) or 'No especificada'}\n"
            f"Paso: {getattr(equine, 'gait', None) or 'No especificado'}\n"
            f"Disponibilidad: {availability_text}"
        )
        source_ref = f"equine:{equine.id}"
        print(f"  - Generando embedding para equino: {equine.name}")
        embedding = await generate_embedding(embedding_client, text)

        upsert_operations.append(
            UpdateOne(
                {"source": source_ref},
                {
                    "$set": {
                        "type": "equine",
                        "title": equine.name,
                        "content": text,
                        "text": text,
                        "scope": "ops",
                        "embedding": embedding,
                        "metadata": {"type": "equine", "id": str(equine.id), "title": equine.name},
                    }
                },
                upsert=True,
            )
        )

    # 3. Políticas
    policies = await PolicyDocument.find_all().to_list()
    for policy in policies:
        text = (
            f"Política de Seguridad / Reserva\n"
            f"Número: {policy.policy_number}\n"
            f"Notas y Protocolo: {getattr(policy, 'notes', None) or 'Sin notas'}"
        )
        source_ref = f"policy:{policy.id}"
        print(f"  - Generando embedding para política: {policy.policy_number}")
        embedding = await generate_embedding(embedding_client, text)

        upsert_operations.append(
            UpdateOne(
                {"source": source_ref},
                {
                    "$set": {
                        "type": "policy",
                        "title": str(getattr(policy, "policy_number", "política")),
                        "content": text,
                        "text": text,
                        "scope": "ops",
                        "embedding": embedding,
                        "metadata": {
                            "type": "policy",
                            "id": str(policy.id),
                            "title": str(getattr(policy, "policy_number", "política")),
                        },
                    }
                },
                upsert=True,
            )
        )

    if upsert_operations:
        collection = KnowledgeDocument.get_motor_collection()
        result = await collection.bulk_write(upsert_operations)
        print(f"Sync complete: {result.upserted_count} upserted, {result.modified_count} modified.")
    else:
        print("No documents to sync.")


if __name__ == "__main__":
    asyncio.run(sync_knowledge())
