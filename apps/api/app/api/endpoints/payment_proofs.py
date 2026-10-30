"""Router de consulta y validacion de comprobantes de pago."""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import get_payment_proof_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import ReservationDocument, UserDocument
from app.schemas.payment_proof import (
    PaymentProofApproveSchema,
    PaymentProofRejectSchema,
    PaymentProofResponseSchema,
    PaymentProofUnrejectSchema,
    PaymentProofUnverifySchema,
    PaymentProofUpdateSchema,
    PaymentProofVerifySchema,
)
from app.schemas.reservation import ReservationResponseSchema
from app.services import PaymentProofService
from app.services.mappers import payment_proof_to_response, reservation_to_response

router = APIRouter(prefix="/payment-proofs", tags=["Comprobantes de pago"])


_DOWNLOAD_RESPONSES = endpoint_responses("payment_proofs_download")
_DOWNLOAD_RESPONSES[202] = {
    "description": "Archivo pendiente de descarga desde WhatsApp.",
    "content": {
        "application/json": {
            "example": {
                "status": "pending",
                "message": "El archivo aun no se ha descargado de WhatsApp. "
                "Intenta de nuevo en unos momentos.",
            }
        }
    },
}


@router.get(
    "/{payment_proof_id}/download",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["payment_proofs_download"]["summary"],
    description=endpoint_description("payment_proofs_download"),
    operation_id="downloadPaymentProofFile",
    responses=_DOWNLOAD_RESPONSES,
)
async def download_payment_proof(
    payment_proof_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_PROOF_READ))],
    service: PaymentProofService = Depends(get_payment_proof_service),
):
    content_type, file_bytes = await service.get_download(payment_proof_id)
    if content_type == "pending":
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "pending",
                "message": "El archivo aun no se ha descargado de WhatsApp. "
                "Intenta de nuevo en unos momentos.",
            },
        )
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="comprobante-{payment_proof_id}"'},
    )


@router.get(
    "/{payment_proof_id}",
    response_model=PaymentProofResponseSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["payment_proofs_get"]["summary"],
    description=endpoint_description("payment_proofs_get"),
    operation_id="getPaymentProofById",
    responses=endpoint_responses("payment_proofs_get"),
)
async def get_payment_proof(
    payment_proof_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_PROOF_READ))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> PaymentProofResponseSchema:
    return payment_proof_to_response(await service.get(payment_proof_id))


@router.patch(
    "/{payment_proof_id}",
    response_model=PaymentProofResponseSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["payment_proofs_update"]["summary"],
    description=endpoint_description("payment_proofs_update"),
    operation_id="updatePaymentProofById",
    responses=endpoint_responses("payment_proofs_update"),
)
async def update_payment_proof(
    payment_proof_id: str,
    payload: PaymentProofUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> PaymentProofResponseSchema:
    return payment_proof_to_response(await service.update(payment_proof_id, payload))


@router.post(
    "/{payment_proof_id}/verify",
    response_model=PaymentProofResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Verificar comprobante de pago",
    operation_id="verifyPaymentProofById",
)
async def verify_payment_proof(
    payment_proof_id: str,
    payload: PaymentProofVerifySchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> PaymentProofResponseSchema:
    return payment_proof_to_response(
        await service.verify_payment(
            payment_proof_id,
            payload,
            actor_id=current_user.id,
            actor_role=current_user.role,
        )
    )


@router.post(
    "/{payment_proof_id}/approve",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Aprobar comprobante de pago y notificar cliente",
    description=(
        "Aprueba el comprobante de pago, actualiza la reserva a PAYMENT_RECEIVED, "
        "genera el enlace del formulario de participantes y notifica al cliente vía WhatsApp."
    ),
    operation_id="approvePaymentProofById",
)
async def approve_payment_proof(
    payment_proof_id: str,
    payload: PaymentProofApproveSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> ReservationResponseSchema:
    proof_doc = await service.approve_payment(
        payment_proof_id,
        payload,
        actor_id=current_user.id,
        actor_role=current_user.role,
    )
    reservation = await ReservationDocument.get(proof_doc.reservation_id)
    return await reservation_to_response(reservation)


@router.post(
    "/{payment_proof_id}/reject",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Rechazar comprobante de pago",
    operation_id="rejectPaymentProofById",
)
async def reject_payment_proof(
    payment_proof_id: str,
    payload: PaymentProofRejectSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> ReservationResponseSchema:
    proof_doc = await service.reject_payment(
        payment_proof_id,
        payload,
        actor_id=current_user.id,
        actor_role=current_user.role,
    )
    reservation = await ReservationDocument.get(proof_doc.reservation_id)
    return await reservation_to_response(reservation)


@router.post(
    "/{payment_proof_id}/unverify",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Deshacer verificacion de comprobante de pago",
    description=(
        "Revoca la verificacion del comprobante. "
        "El comprobante y la reserva vuelven a estado 'received' (no verificado)."
    ),
    operation_id="unverifyPaymentProofById",
)
async def unverify_payment_proof(
    payment_proof_id: str,
    payload: PaymentProofUnverifySchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> ReservationResponseSchema:
    proof_doc = await service.unverify_payment(
        payment_proof_id,
        payload,
        actor_id=current_user.id,
        actor_role=current_user.role,
    )
    reservation = await ReservationDocument.get(proof_doc.reservation_id)
    return await reservation_to_response(reservation)


@router.post(
    "/{payment_proof_id}/unreject",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Deshacer rechazo de comprobante de pago",
    description=(
        "Revoca el rechazo del comprobante. "
        "El comprobante y la reserva vuelven a estado 'received'."
    ),
    operation_id="unrejectPaymentProofById",
)
async def unreject_payment_proof(
    payment_proof_id: str,
    payload: PaymentProofUnrejectSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
    service: PaymentProofService = Depends(get_payment_proof_service),
) -> ReservationResponseSchema:
    proof_doc = await service.unreject_payment(
        payment_proof_id,
        payload,
        actor_id=current_user.id,
        actor_role=current_user.role,
    )
    reservation = await ReservationDocument.get(proof_doc.reservation_id)
    return await reservation_to_response(reservation)
