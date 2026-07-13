from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.labels import ErrorCode
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


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    fields = []
    for error in exc.errors():
        serializable_error = dict(error)
        serializable_error.pop("ctx", None)
        fields.append(serializable_error)
    payload = ApiErrorResponse(
        code=ErrorCode.VALIDATION_ERROR,
        message="La solicitud contiene datos inválidos.",
        details={"fields": fields},
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        payload = ApiErrorResponse(
            code=exc.detail["code"],
            message=exc.detail["message"],
            details=exc.detail.get("details"),
        )
    else:
        payload = ApiErrorResponse(
            code=ErrorCode.INTERNAL_ERROR if exc.status_code >= 500 else ErrorCode.CONFLICT,
            message=str(exc.detail),
            details=None,
        )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
