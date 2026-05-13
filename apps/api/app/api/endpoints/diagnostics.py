from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.time import now_colombia, today_colombia_iso
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


@router.get("/time")
async def get_time_diagnostics() -> dict:
    now_co = now_colombia()
    now_utc = datetime.now(UTC)

    return {
        "utc": now_utc.isoformat(),
        "colombia": now_co.isoformat(),
        "colombia_date": today_colombia_iso(),
        "timezone": "America/Bogota",
    }
