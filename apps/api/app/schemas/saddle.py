from pydantic import BaseModel


class SaddleCreateSchema(BaseModel):
    code: str
    name: str | None = None
    is_available: bool = True
    notes: str | None = None


class SaddleUpdateSchema(BaseModel):
    code: str | None = None
    name: str | None = None
    is_available: bool | None = None
    notes: str | None = None


class SaddleResponseSchema(BaseModel):
    id: str
    code: str
    name: str | None
    is_available: bool
    notes: str | None
