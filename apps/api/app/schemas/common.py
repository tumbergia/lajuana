from typing import Any

from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
