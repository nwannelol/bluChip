"""NEXUS LangGraph orchestrator.

Builds and compiles the StateGraph that routes every incoming message
to the correct agent node (fan / media / scout / ops).

Usage:
    from app.graph.orchestrator import build_graph
    graph = build_graph(settings)
    result = await graph.ainvoke(state)
"""

from langgraph.graph import END, START, StateGraph

from app.config import Settings
from app.graph.nodes import make_nodes, route_message
from app.graph.state import NEXUSState


def build_graph(settings: Settings):
    """Compile and return the NEXUS StateGraph."""
    nodes = make_nodes(settings)

    graph: StateGraph = StateGraph(NEXUSState)

    for name, fn in nodes.items():
        graph.add_node(name, fn)

    graph.add_conditional_edges(START, route_message, {k: k for k in nodes})

    for name in nodes:
        graph.add_edge(name, END)

    return graph.compile()
