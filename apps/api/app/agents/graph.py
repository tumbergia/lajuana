from functools import partial

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.nodes import (
    NodeDependencies,
    default_dependencies,
    map_role_for_graph,
    now_iso,
    ops_agent_node,
    route_initial_by_role,
    tourist_agent_node,
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
        )
    )
    tourist_tools_node = ToolNode(create_tourist_tools(deps.booking_service, deps.vector_client))

    workflow = StateGraph(GraphState)
    
    workflow.add_node("ops_agent", partial(ops_agent_node, deps=deps))
    workflow.add_node("ops_tools", ops_tools_node)
    
    workflow.add_node("tourist_agent", partial(tourist_agent_node, deps=deps))
    workflow.add_node("tourist_tools", tourist_tools_node)

    workflow.add_conditional_edges(
        START,
        route_initial_by_role,
        {
            "ops_agent": "ops_agent",
            "tourist_agent": "tourist_agent",
        }
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

    workflow.add_conditional_edges(
        "tourist_agent",
        tools_condition,
        {
            "tools": "tourist_tools",
            "__end__": END,
        },
    )
    workflow.add_edge("tourist_tools", "tourist_agent")

    return workflow.compile()

_graph = build_chat_graph()

def get_chat_graph():
    return _graph
