from langgraph.graph import END, START, StateGraph

from app.agent.nodes.analyzer import analyzer_node
from app.agent.nodes.deployer import deployer_node
from app.agent.nodes.generator import generator_node
from app.agent.nodes.planner import planner_node
from app.agent.nodes.validator import validator_node
from app.agent.nodes.writer import writer_node
from app.agent.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("analyzer", analyzer_node)
    graph.add_node("planner", planner_node)
    graph.add_node("generator", generator_node)
    graph.add_node("validator", validator_node)
    graph.add_node("writer", writer_node)
    graph.add_node("deployer", deployer_node)

    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "planner")
    graph.add_edge("planner", "generator")
    graph.add_edge("generator", "validator")
    graph.add_edge("validator", "writer")
    graph.add_edge("writer", "deployer")
    graph.add_edge("deployer", END)

    return graph


agent = build_graph().compile()
