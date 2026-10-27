"""
routing.py
==========
Routing logic for LangGraph orchestrator.
Directs flow conditionally based on the orchestrator's execution plan.
"""
from typing import Literal
from app.graph.state import AgentState

def route_orchestrator(state: AgentState) -> Literal["statistical", "ml", "sql", "visualization"]:
    targets = state.get("target_agents", [])
    if "ml_agent" in targets:
        return "ml"
    elif "sql_agent" in targets:
        return "sql"
    elif "statistical_agent" in targets:
        return "statistical"
    elif "visualization_agent" in targets:
        return "visualization"
    return "statistical"
