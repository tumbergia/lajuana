import base64
from pathlib import Path

from app.core.config import settings


class LocalStorageAdapter:
    def __init__(self) -> None:
        self.root = Path(settings.storage_local_root)
        self.prefix = settings.storage_local_payment_proofs_prefix

    async def store_base64(self, *, reservation_id: str, filename: str, content_base64: str) -> str:
        directory = self.root / self.prefix / reservation_id
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / filename
        file_path.write_bytes(base64.b64decode(content_base64))
        return str(file_path.relative_to(self.root))
