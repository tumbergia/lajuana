"""Pobla el campo file_data de PaymentProofDocument con bytes reales.

Busca comprobantes cuyo storage_key comience con 'synthetic/' o 'seed/'
y que no tengan file_data, y les asigna los bytes de la imagen local.

Uso:
    cd apps/api
    python -m app.seed_proof_file_data
"""

import asyncio
import hashlib
from pathlib import Path

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient as AsyncMotorClient

from app.core.config import settings
from app.documents import PaymentProofDocument

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # C:\dev\lajuana

# Mapa de storage_key → ruta local del archivo
SYNTHETIC_FILE_MAP: dict[str, Path] = {
    "synthetic/pago-example.png": PROJECT_ROOT / "pago-example.png",
}


async def main() -> None:
    client = AsyncMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    await init_beanie(
        database=db,
        document_models=[PaymentProofDocument],
    )

    # Probar archivos locales primero
    for storage_key, local_path in SYNTHETIC_FILE_MAP.items():
        if not local_path.exists():
            print(f"[ERROR] Archivo local no encontrado: {local_path}")
            continue

        proof = await PaymentProofDocument.find_one({"storage_key": storage_key, "file_data": None})
        if proof is None:
            print(f"[SKIP] {storage_key}: no existe o ya tiene file_data")
            continue

        file_bytes = local_path.read_bytes()
        content_type = _guess_content_type(local_path.name)
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()

        proof.file_data = file_bytes
        proof.size_bytes = len(file_bytes)
        proof.sha256 = sha256_hash
        if content_type:
            proof.content_type = content_type

        await proof.save()
        print(
            f"[OK] {storage_key}: {len(file_bytes)} bytes -> file_data "
            f"(content_type={content_type}, sha256={sha256_hash[:16]}...)"
        )

    # Buscar proofs con storage_key "seed/" sin file_data (seed_reproducible)
    seed_proofs = await PaymentProofDocument.find(
        {"storage_key": {"$regex": "^seed/"}, "file_data": None}
    ).to_list()
    for proof in seed_proofs:
        print(f"[WARN] {proof.storage_key}: no hay archivo real mapeado. Generando placeholder.")
        placeholder = b"PV"  # Tiny placeholder — will show as broken image
        proof.file_data = placeholder
        proof.size_bytes = len(placeholder)
        proof.sha256 = hashlib.sha256(placeholder).hexdigest()
        await proof.save()
        print(f"[OK] {proof.storage_key}: placeholder asignado ({len(placeholder)} bytes)")

    client.close()
    print("[DONE] seed_proof_file_data completado.")


def _guess_content_type(filename: str) -> str | None:
    ext = Path(filename).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
    }.get(ext)


if __name__ == "__main__":
    asyncio.run(main())
