"""Server-owned analytics module catalog, filtered by permissions."""

from __future__ import annotations

from datetime import UTC, datetime

from app.common.enums import ROLE_PERMISSIONS, Permission, UserRole
from app.schemas.analytics_v2 import (
    ANALYTICS_SCHEMA_VERSION,
    CatalogModule,
    CatalogModuleSize,
    CatalogResponse,
    DateRangePreset,
    ModuleCategory,
    VisualizationType,
)

_ALL_RANGES = [
    DateRangePreset.LAST_7_DAYS,
    DateRangePreset.LAST_30_DAYS,
    DateRangePreset.LAST_3_MONTHS,
    DateRangePreset.THIS_YEAR,
    DateRangePreset.CUSTOM,
]

_STANDARD_SIZES = [
    CatalogModuleSize.COMPACT,
    CatalogModuleSize.STANDARD,
]


def _mod(
    *,
    id: str,
    category: ModuleCategory,
    title: str,
    description: str,
    viz: VisualizationType,
    permission: Permission,
    home_configurable: bool = True,
    always_show_when_active: bool = False,
    blocked: bool = False,
    blocked_reason: str | None = None,
    sizes: list[CatalogModuleSize] | None = None,
) -> CatalogModule:
    return CatalogModule(
        id=id,
        category=category,
        title=title,
        description=description,
        recommended_visualization=viz,
        supported_ranges=_ALL_RANGES,
        allowed_sizes=sizes or list(_STANDARD_SIZES),
        required_permission=permission.value,
        home_configurable=home_configurable,
        always_show_when_active=always_show_when_active,
        blocked=blocked,
        blocked_reason=blocked_reason,
    )


CATALOG: list[CatalogModule] = [
    _mod(
        id="action_center",
        category=ModuleCategory.ACTION,
        title="Tareas pendientes",
        description="Pendientes que requieren acción inmediata.",
        viz=VisualizationType.ACTION_LIST,
        permission=Permission.RESERVATION_READ,
        home_configurable=False,
        always_show_when_active=True,
    ),
    _mod(
        id="reservation_trend",
        category=ModuleCategory.RESERVATIONS,
        title="Tendencia de reservas",
        description="Cómo evolucionan las reservas nuevas en el periodo.",
        viz=VisualizationType.LINE,
        permission=Permission.RESERVATION_READ,
    ),
    _mod(
        id="reservation_status",
        category=ModuleCategory.RESERVATIONS,
        title="Estado de las reservas",
        description="Distribución de reservas por estado en el periodo.",
        viz=VisualizationType.DONUT,
        permission=Permission.RESERVATION_READ,
    ),
    _mod(
        id="reservation_origins",
        category=ModuleCategory.RESERVATIONS,
        title="Orígenes de reserva",
        description="De dónde llegan las reservas nuevas (WhatsApp, redes, correo).",
        viz=VisualizationType.DONUT,
        permission=Permission.RESERVATION_READ,
    ),
    _mod(
        id="confirmed_value_trend",
        category=ModuleCategory.MONEY,
        title="Ingresos comprometidos",
        description=(
            "Monto cotizado de reservas confirmadas o completadas: lo que ya está "
            "asegurado para facturar, aunque el pago todavía no se haya recibido."
        ),
        viz=VisualizationType.LINE,
        permission=Permission.RESERVATION_READ,
    ),
    _mod(
        id="payment_status",
        category=ModuleCategory.MONEY,
        title="Comprobantes de pago",
        description="Estado de los comprobantes recibidos.",
        viz=VisualizationType.DONUT,
        permission=Permission.PAYMENT_PROOF_READ,
    ),
    _mod(
        id="top_experiences",
        category=ModuleCategory.EXPERIENCES,
        title="Experiencias más reservadas",
        description="Experiencias con más reservas confirmadas o completadas.",
        viz=VisualizationType.RANKING,
        permission=Permission.EXPERIENCE_READ,
    ),
    _mod(
        id="occupancy",
        category=ModuleCategory.OPERATIONS,
        title="Ocupación de próximas salidas",
        description="Participantes confirmados frente al cupo de cada experiencia.",
        viz=VisualizationType.PROGRESS,
        permission=Permission.RESERVATION_READ,
    ),
    _mod(
        id="top_countries",
        category=ModuleCategory.PARTICIPANTS,
        title="Países de los visitantes",
        description="Países de residencia de participantes en reservas confirmadas o completadas.",
        viz=VisualizationType.RANKING,
        permission=Permission.PARTICIPANT_READ,
    ),
    _mod(
        id="participant_readiness",
        category=ModuleCategory.PARTICIPANTS,
        title="Preparación de participantes",
        description="Participantes pendientes de registrar en salidas próximas confirmadas.",
        viz=VisualizationType.PROGRESS,
        permission=Permission.PARTICIPANT_READ,
    ),
    _mod(
        id="equine_availability",
        category=ModuleCategory.EQUINES,
        title="Disponibilidad equina",
        description="Cuántas mulas y equinos están disponibles para asignar.",
        viz=VisualizationType.DONUT,
        permission=Permission.EQUINE_READ,
    ),
    _mod(
        id="equine_workload",
        category=ModuleCategory.EQUINES,
        title="Carga de trabajo equina",
        description="Distribución de la carga entre equinos en el periodo.",
        viz=VisualizationType.RANKING,
        permission=Permission.EQUINE_READ,
    ),
    _mod(
        id="equine_care_alerts",
        category=ModuleCategory.EQUINES,
        title="Alertas de cuidados",
        description="Cuidados vencidos o próximos y alertas de bienestar.",
        viz=VisualizationType.ACTION_LIST,
        permission=Permission.EQUINE_READ,
    ),
]

# Documented blocked concepts (not shipped as modules until data exists).
BLOCKED_CONCEPTS = {
    "commercial_conversion": (
        "No hay historial de embudo por cohorte suficiente para una "
        "tasa de conversión comercial defendible."
    ),
    "collected_revenue": (
        "Los comprobantes de pago no registran montos; solo existe "
        "valor cotizado y valor confirmado."
    ),
}

# Legacy lead pin → v2 module (only valid equivalences).
LEGACY_LEAD_TO_MODULE: dict[str, str] = {
    "ing_confirmed": "confirmed_value_trend",
    "vol_confirmed": "reservation_status",
    "vol_activas": "reservation_trend",
    "vol_completed": "reservation_status",
    "exp_top": "top_experiences",
    "ori_top_pais": "top_countries",
    "ori_top_5": "top_countries",
    "ori_top_pct": "top_countries",
    "par_pending": "participant_readiness",
    "par_completed": "participant_readiness",
    "eq_available": "equine_availability",
    "eq_in_service": "equine_availability",
    "eq_workload": "equine_workload",
    "eq_overdue_care": "equine_care_alerts",
    "eq_due_soon": "equine_care_alerts",
    "eq_injured": "equine_care_alerts",
    "eq_open_injuries": "equine_care_alerts",
    "eq_high_severity": "equine_care_alerts",
    "pay_received": "payment_status",
    "pay_pending": "payment_status",
    "pay_verified": "payment_status",
    "vol_pending_payment": "action_center",
    "vol_payment_received": "action_center",
    "vol_contact": "action_center",
    "vol_quoted": "action_center",
}

ADMIN_DEFAULT_MODULES = [
    "confirmed_value_trend",
    "reservation_status",
    "top_experiences",
    "top_countries",
]

GUIDE_DEFAULT_MODULES = [
    "occupancy",
    "participant_readiness",
    "equine_availability",
    "equine_care_alerts",
]


class AnalyticsCatalogService:
    def get_catalog(self, role: UserRole) -> CatalogResponse:
        perms = ROLE_PERMISSIONS.get(role, set())
        modules: list[CatalogModule] = []
        for mod in CATALOG:
            try:
                required = Permission(mod.required_permission)
            except ValueError:
                continue
            if required in perms:
                modules.append(mod)
        return CatalogResponse(
            modules=modules,
            schema_version=ANALYTICS_SCHEMA_VERSION,
            generated_at=datetime.now(UTC),
        )

    def allowed_module_ids(self, role: UserRole) -> set[str]:
        return {m.id for m in self.get_catalog(role).modules}

    def defaults_for_role(self, role: UserRole) -> list[str]:
        allowed = self.allowed_module_ids(role)
        if role == UserRole.GUIDE:
            candidates = GUIDE_DEFAULT_MODULES
        else:
            candidates = ADMIN_DEFAULT_MODULES
        return [m for m in candidates if m in allowed][:4]

    def map_legacy_pins(self, pinned_lead_ids: list[str], role: UserRole) -> list[str]:
        allowed = self.allowed_module_ids(role)
        mapped: list[str] = []
        seen: set[str] = set()
        for lead_id in pinned_lead_ids:
            module_id = LEGACY_LEAD_TO_MODULE.get(lead_id)
            if not module_id or module_id not in allowed or module_id in seen:
                continue
            # action_center is auto; skip as configurable pin
            if module_id == "action_center":
                continue
            seen.add(module_id)
            mapped.append(module_id)
            if len(mapped) >= 4:
                break
        return mapped
