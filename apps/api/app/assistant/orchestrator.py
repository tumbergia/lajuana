from uuid import uuid4

from app.assistant.intent_detector import detect_intent
from app.assistant.response_composer import (
    compose_availability_response,
    compose_general_response,
    compose_missing_data_response,
)
from app.assistant.trace import complete_turn, create_inbound_turn
from app.mcp_server import registry
from app.schemas.ask import AskRequest, AskResponse


class AssistantOrchestrator:
    async def ask(self, request: AskRequest) -> AskResponse:
        trace_id = request.trace_id or str(uuid4())

        turn = await create_inbound_turn(
            channel=request.channel,
            message=request.message,
            from_phone=request.from_phone,
            trace_id=trace_id,
        )

        intent = detect_intent(request.message)

        if intent.name == "availability_check" and not intent.requires_tool:
            response = compose_missing_data_response(intent)
            await complete_turn(turn, detected_intent=intent.name, response_text=response)

            return AskResponse(
                trace_id=trace_id,
                intent=intent.name,
                requires_tool=False,
                response=response,
            )

        if intent.requires_tool and intent.tool_name == "check_experience_availability":
            tool_input = {
                "experience_query": intent.experience_query,
                "requested_date": intent.requested_date.isoformat()
                if intent.requested_date
                else None,
                "participant_count": intent.participant_count or 1,
                "trace_id": trace_id,
                "conversation_turn_id": str(turn.id),
            }

            tool_output = await registry.call("check_experience_availability", **tool_input)
            response = compose_availability_response(tool_output)

            await complete_turn(turn, detected_intent=intent.name, response_text=response)

            return AskResponse(
                trace_id=trace_id,
                intent=intent.name,
                requires_tool=True,
                tool_name="check_experience_availability",
                tool_input=tool_input,
                tool_output=tool_output,
                response=response,
            )

        response = compose_general_response()
        await complete_turn(turn, detected_intent=intent.name, response_text=response)

        return AskResponse(
            trace_id=trace_id,
            intent=intent.name,
            requires_tool=False,
            response=response,
        )
