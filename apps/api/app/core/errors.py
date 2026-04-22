from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.common import ApiErrorResponse


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    payload = ApiErrorResponse(
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
