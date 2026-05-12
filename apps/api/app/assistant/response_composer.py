from typing import Any

from app.assistant.intent_detector import DetectedIntent


def compose_missing_data_response(intent: DetectedIntent) -> str:
    missing: list[str] = []

    if intent.requested_date is None:
        missing.append("la fecha")
    if intent.participant_count is None:
        missing.append("el número de personas")
    if intent.experience_query is None:
        missing.append("la experiencia o tipo de recorrido")

    if not missing:
        return "Necesito un dato adicional para revisar disponibilidad."

    joined = ", ".join(missing)
    return f"Para revisar disponibilidad necesito: {joined}."


def compose_availability_response(tool_output: dict[str, Any]) -> str:
    if tool_output.get("available") is True:
        experience_name = tool_output.get("experience_name") or "esa experiencia"
        requested_date = tool_output.get("requested_date")
        participant_count = tool_output.get("participant_count")
        capacity_available = tool_output.get("capacity_available")

        return (
            f"Sí, hay disponibilidad para {experience_name} el {requested_date} "
            f"para {participant_count} persona(s). Cupos disponibles: {capacity_available}. "
            "Esto todavía no confirma la reserva; para avanzar habría que generar la cotización "
            "y luego validar el pago."
        )

    reasons = tool_output.get("blocking_reasons") or []
    if not reasons:
        return "No pude confirmar disponibilidad con la información disponible."

    main_reason = reasons[0]
    message = main_reason.get("message") or "No hay disponibilidad para esa solicitud."
    return f"No puedo avanzar con esa fecha: {message}"


def compose_general_response() -> str:
    return (
        "Puedo ayudarte a revisar disponibilidad de experiencias. "
        "Envíame tipo de experiencia, fecha y número de personas."
    )
