"""Base CRUD genérica para servicios con get-or-404, create, update, soft_delete, list, count.

Cada servicio específico extiende esta clase y solo agrega validación de dominio.
Elimina ~80% del boilerplate CRUD repetitivo (issue A4 del plan de mejora).
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from beanie import Document as BeanieDocument
from pydantic import BaseModel

from app.common.labels import ErrorCode
from app.core.errors import ApiError

# Type variables for document, create schema, and update schema
DocT = TypeVar("DocT", bound=BeanieDocument)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class BaseService(Generic[DocT, CreateSchemaT, UpdateSchemaT]):
    """CRUD genérico con métodos base reutilizables.

    Subclases deben definir:
        document_class   → la clase del documento Beanie
        not_found_code   → ErrorCode para 404 (ej: ErrorCode.SADDLE_NOT_FOUND)
        not_found_message → mensaje de error para 404

    Subclases pueden sobreescribir:
        create()  — para validación adicional antes de insertar
        update()  — para validación adicional antes de guardar
        list()    — si tiene filtros específicos de dominio

    Subclases agregan:
        Métodos de negocio específicos (list_available, restore, etc.)
    """

    document_class: type[DocT]
    not_found_code: str = ErrorCode.RESOURCE_NOT_FOUND
    not_found_message: str = "Recurso no encontrado."

    # ── READ ──

    async def get(self, doc_id: str) -> DocT:
        """Retorna documento por ID. ApiError 404 si no existe."""
        doc = await self.document_class.get(doc_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=self.not_found_code,
                message=self.not_found_message,
            )
        return doc

    async def list(
        self,
        include_deleted: bool = False,
        limit: int = 200,
        skip: int = 0,
    ) -> list[DocT]:
        """Lista documentos con paginación, excluyendo borrados lógicos por defecto."""
        query: dict[str, Any] = {}
        if not include_deleted:
            query["deleted_at"] = None
        return await self.document_class.find(query).skip(skip).limit(limit).to_list()

    async def count(
        self,
        include_deleted: bool = False,
    ) -> int:
        """Cuenta documentos, excluyendo borrados lógicos por defecto."""
        query: dict[str, Any] = {}
        if not include_deleted:
            query["deleted_at"] = None
        return await self.document_class.find(query).count()

    # ── CREATE ──

    async def create(self, payload: CreateSchemaT) -> DocT:
        """Crea un documento a partir del schema de creación."""
        doc = self.document_class(**payload.model_dump())
        await doc.insert()
        return doc

    # ── UPDATE ──

    async def update(self, doc_id: str, payload: UpdateSchemaT) -> DocT:
        """Actualiza parcialmente un documento (solo campos no-None del schema)."""
        doc = await self.get(doc_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(doc, field, value)
        await doc.save()
        return doc

    # ── SOFT DELETE ──

    async def soft_delete(self, doc_id: str) -> DocT:
        """Borra lógicamente: marca deleted_at. No elimina físicamente."""
        doc = await self.get(doc_id)
        doc.deleted_at = datetime.now(UTC)
        await doc.save()
        return doc

    async def restore(self, doc_id: str) -> DocT:
        """Restaura un documento borrado lógicamente."""
        doc = await self.get(doc_id)
        doc.deleted_at = None
        await doc.save()
        return doc
