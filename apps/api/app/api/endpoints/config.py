from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_config_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.config import (
    AiConfigurationSchema,
    AiConfigurationUpdateSchema,
    BusinessLocationSchema,
    BusinessLocationUpdateSchema,
    ConfigurationSummarySchema,
    EmergencyContactsResponseSchema,
    PaymentInstructionsSchema,
    PaymentInstructionsUpdateSchema,
    ReservationRulesSchema,
    ReservationRulesUpdateSchema,
)
from app.services import ConfigService

router = APIRouter(prefix="/config", tags=["Configuracion"])


@router.get(
    "/emergency-contacts",
    response_model=EmergencyContactsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["config_emergency_contacts"]["summary"],
    description=endpoint_description("config_emergency_contacts"),
    operation_id="getEmergencyContacts",
    responses=endpoint_responses("config_emergency_contacts"),
)
async def get_emergency_contacts(
    service: ConfigService = Depends(get_config_service),
) -> EmergencyContactsResponseSchema:
    return await service.get_emergency_contacts()


@router.get(
    "/reservation-rules",
    response_model=ReservationRulesSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["config_get"]["summary"],
    description=endpoint_description("config_get"),
    operation_id="getReservationRules",
    responses=endpoint_responses("config_get"),
)
async def get_reservation_rules(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
    service: ConfigService = Depends(get_config_service),
) -> ReservationRulesSchema:
    return await service.get_reservation_rules()


@router.patch(
    "/reservation-rules",
    response_model=ReservationRulesSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["config_update"]["summary"],
    description=endpoint_description("config_update"),
    operation_id="updateReservationRules",
    responses=endpoint_responses("config_update"),
)
async def update_reservation_rules(
    payload: ReservationRulesUpdateSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_UPDATE))],
    service: ConfigService = Depends(get_config_service),
) -> ReservationRulesSchema:
    return await service.update_reservation_rules(payload, actor_id=current_user.id)


@router.get("/summary", response_model=ConfigurationSummarySchema)
async def get_configuration_summary(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
    service: ConfigService = Depends(get_config_service),
) -> ConfigurationSummarySchema:
    return await service.get_summary()


@router.get("/ai", response_model=AiConfigurationSchema)
async def get_ai_configuration(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
    service: ConfigService = Depends(get_config_service),
) -> AiConfigurationSchema:
    return await service.get_ai_configuration()


@router.patch("/ai", response_model=AiConfigurationSchema)
async def update_ai_configuration(
    payload: AiConfigurationUpdateSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_UPDATE))],
    service: ConfigService = Depends(get_config_service),
) -> AiConfigurationSchema:
    return await service.update_ai_configuration(payload, actor_id=current_user.id)


@router.get("/payment-methods", response_model=PaymentInstructionsSchema)
async def get_payment_methods(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
    service: ConfigService = Depends(get_config_service),
) -> PaymentInstructionsSchema:
    return await service.get_payment_instructions()


@router.patch("/payment-methods", response_model=PaymentInstructionsSchema)
async def update_payment_methods(
    payload: PaymentInstructionsUpdateSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_UPDATE))],
    service: ConfigService = Depends(get_config_service),
) -> PaymentInstructionsSchema:
    return await service.update_payment_instructions(payload, actor_id=current_user.id)


@router.get("/business-location", response_model=BusinessLocationSchema)
async def get_business_location(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
    service: ConfigService = Depends(get_config_service),
) -> BusinessLocationSchema:
    return await service.get_business_location()


@router.patch("/business-location", response_model=BusinessLocationSchema)
async def update_business_location(
    payload: BusinessLocationUpdateSchema,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_UPDATE))],
    service: ConfigService = Depends(get_config_service),
) -> BusinessLocationSchema:
    return await service.update_business_location(payload, actor_id=current_user.id)
