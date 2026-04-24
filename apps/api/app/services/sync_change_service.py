from app.documents import SyncChangeDocument

STREAM_BY_COLLECTION = {
    "reservations": "reservations",
    "participants": "participants",
    "payment_proofs": "payment_proofs",
    "assignments": "assignments",
    "service_logs": "logs",
    "providers": "providers",
    "policies": "policies",
    "schedules": "schedules",
    "equines": "equines",
    "experiences": "experiences",
    "users": "users",
    "app_config": "config",
}


async def record_document_change(document, *, change_type: str = "upsert") -> None:
    collection_name = getattr(getattr(document, "Settings", object), "name", "")
    stream = STREAM_BY_COLLECTION.get(collection_name)
    if stream is None or getattr(document, "id", None) is None:
        return

    payload = document.model_dump(mode="json")
    payload["id"] = str(document.id)
    change = SyncChangeDocument(
        stream=stream,
        entity_type=document.__class__.__name__.replace("Document", "").lower(),
        entity_id=str(document.id),
        change_type="delete" if change_type == "delete" else "upsert",
        version=getattr(document, "version", 1),
        entity_updated_at=document.updated_at,
        payload=payload,
    )
    await change.insert()
