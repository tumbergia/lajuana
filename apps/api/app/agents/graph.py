from functools import partial

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    NodeDependencies,
    booking_node,
    classify_intent_node,
    default_dependencies,
    extract_ops_node,
    ops_feedback_node,
    rag_answer_node,
    rag_node,
    route_initial_by_role,
    route_ops_validation,
    route_tourist_intent,
    save_ops_node,
    validate_ops_node,
)
from app.agents.state import GraphState


def build_chat_graph(dependencies: NodeDependencies | None = None):
    deps = dependencies or default_dependencies()

    workflow = StateGraph(GraphState)
    workflow.add_node("extract_ops", partial(extract_ops_node, deps=deps))
    workflow.add_node("validate_ops", validate_ops_node)
    workflow.add_node("ops_feedback", ops_feedback_node)
    workflow.add_node("save_ops", partial(save_ops_node, deps=deps))

    workflow.add_node("rag", partial(rag_node, deps=deps))
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("rag_answer", rag_answer_node)
    workflow.add_node("booking", partial(booking_node, deps=deps))

    workflow.add_conditional_edges(
        START,
        route_initial_by_role,
        {
            "ops": "extract_ops",
            "tourist": "rag",
        },
    )

    workflow.add_edge("extract_ops", "validate_ops")
    workflow.add_conditional_edges(
        "validate_ops",
        route_ops_validation,
        {
            "save": "save_ops",
            "feedback": "ops_feedback",
        },
    )
    workflow.add_edge("save_ops", END)
    workflow.add_edge("ops_feedback", END)

    workflow.add_edge("rag", "classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        route_tourist_intent,
        {
            "booking": "booking",
            "answer": "rag_answer",
        },
    )
    workflow.add_edge("booking", END)
    workflow.add_edge("rag_answer", END)

    return workflow.compile()


_graph = build_chat_graph()


def get_chat_graph():
    return _graph
