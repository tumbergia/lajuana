from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.nodes import (
    NodeDependencies,
    default_dependencies,
    ops_agent_node,
    route_initial_by_role,
)
from app.agents.reservation_nodes import (
    check_availability_node,
    classify_intent_node,
    collect_missing_data_node,
    create_reservation_node,
    extract_entities_node,
    receive_message_node,
    respond_to_user_node,
    retrieve_context_node,
    sync_knowledge_node,
)
from app.agents.state import GraphState
from app.agents.tools import create_ops_tools, create_tourist_tools


def build_chat_graph(dependencies: NodeDependencies | None = None):
    deps = dependencies or default_dependencies()

    # Create distinct tool nodes for each flow
    ops_tools_node = ToolNode(
        create_ops_tools(
            ops_service=deps.ops_service,
            reservation_service=deps.reservation_service,
            participant_service=deps.participant_service,
            equine_service=deps.equine_service,
            schedule_service=deps.schedule_service,
            saddle_service=deps.saddle_service,
            vector_client=deps.vector_client,
        )
    )

    workflow = StateGraph(GraphState)

    workflow.add_node("ops_agent", partial(ops_agent_node, deps=deps))
    workflow.add_node("ops_tools", ops_tools_node)

    workflow.add_node("reservation_receive_message", partial(receive_message_node, deps=deps))
    workflow.add_node("reservation_classify_intent", partial(classify_intent_node, deps=deps))
    workflow.add_node("reservation_extract_entities", partial(extract_entities_node, deps=deps))
    workflow.add_node("reservation_retrieve_context", partial(retrieve_context_node, deps=deps))
    workflow.add_node("reservation_check_availability", partial(check_availability_node, deps=deps))
    workflow.add_node("reservation_collect_missing_data", partial(collect_missing_data_node, deps=deps))
    workflow.add_node("reservation_create_reservation", partial(create_reservation_node, deps=deps))
    workflow.add_node("reservation_sync_knowledge", partial(sync_knowledge_node, deps=deps))
    workflow.add_node("reservation_respond_to_user", partial(respond_to_user_node, deps=deps))

    workflow.add_conditional_edges(
        START,
        route_initial_by_role,
        {
            "ops_agent": "ops_agent",
            "reservation_receive_message": "reservation_receive_message",
        },
    )

    workflow.add_conditional_edges(
        "ops_agent",
        tools_condition,
        {
            "tools": "ops_tools",
            "__end__": END,
        },
    )
    workflow.add_edge("ops_tools", "ops_agent")

    workflow.add_edge("reservation_receive_message", "reservation_classify_intent")
    workflow.add_edge("reservation_classify_intent", "reservation_extract_entities")
    workflow.add_edge("reservation_extract_entities", "reservation_retrieve_context")
    workflow.add_edge("reservation_retrieve_context", "reservation_check_availability")
    workflow.add_edge("reservation_check_availability", "reservation_collect_missing_data")
    workflow.add_edge("reservation_collect_missing_data", "reservation_create_reservation")
    workflow.add_edge("reservation_create_reservation", "reservation_sync_knowledge")
    workflow.add_edge("reservation_sync_knowledge", "reservation_respond_to_user")
    workflow.add_edge("reservation_respond_to_user", END)

    return workflow.compile()


_graph = build_chat_graph()


def get_chat_graph():
    return _graph
