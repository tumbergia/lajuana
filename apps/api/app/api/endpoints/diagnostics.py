from fastapi import APIRouter

from app.documents.ping_document import PingDocument

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.post("/ping")
async def create_ping() -> dict[str, str]:
    doc = PingDocument(name="mongo-beanie-check")
    await doc.insert()
    return {"status": "inserted"}


@router.get("/ping/latest")
async def get_latest_ping() -> dict[str, str | bool]:
    doc = await PingDocument.find_one(sort=[("id", -1)])
    if doc is None:
        return {"status": "empty", "ok": False}
    return {"status": doc.name, "ok": doc.ok}
