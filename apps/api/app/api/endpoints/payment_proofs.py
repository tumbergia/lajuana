"""Router de consulta y validacion de comprobantes de pago."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.payment_proof import PaymentProofResponseSchema, PaymentProofUpdateSchema
from app.services import PaymentProofService
from app.services.mappers import payment_proof_to_response

router = APIRouter(prefix="/payment-proofs", tags=["Comprobantes de pago"])
service = PaymentProofService()


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
) -> PaymentProofResponseSchema:
    return payment_proof_to_response(await service.update(payment_proof_id, payload))
