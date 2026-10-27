"""
workflow.py
===========
Compiles the LangGraph StateGraph connecting the Orchestrator, SQL, Statistical,
ML, Visualization, and Synthesis agents into an executable analytical pipeline.
"""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Dict, Optional
from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentState
from app.graph.nodes import (
    orchestrator_node,
    statistical_node,
    ml_node,
    sql_node,
    visualization_node,
    synthesis_node
)
from app.graph.routing import route_orchestrator

def build_analyst_graph():
    builder = StateGraph(AgentState)

    # 1. Add all agent nodes
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("statistical", statistical_node)
    builder.add_node("ml", ml_node)
    builder.add_node("sql", sql_node)
    builder.add_node("visualization", visualization_node)
    builder.add_node("synthesis", synthesis_node)

    # 2. Add edges
    builder.add_edge(START, "orchestrator")

    # Conditional routing from orchestrator to the primary analytical agent
    builder.add_conditional_edges(
        "orchestrator",
        route_orchestrator,
        {
            "statistical": "statistical",
            "ml": "ml",
            "sql": "sql",
            "visualization": "visualization",
        }
    )

    # All primary analytical agents flow to visualization
    builder.add_edge("statistical", "visualization")
    builder.add_edge("ml", "visualization")
    builder.add_edge("sql", "visualization")

    # Visualization flows to synthesis
    builder.add_edge("visualization", "synthesis")

    # Synthesis finishes the workflow
    builder.add_edge("synthesis", END)

    return builder.compile()

analyst_graph = build_analyst_graph()

async def stream_workflow_events(
    initial_state: AgentState
) -> AsyncGenerator[str, None]:
    """
    Streams Server-Sent Events (SSE) detailing real agent execution progress
    and yields the final synthesized response at the end.
    """
    last_event_count = 0
    current_state = dict(initial_state)

    for output in analyst_graph.stream(initial_state):
        for node_name, node_update in output.items():
            current_state.update(node_update)
            events = current_state.get("progress_events", [])
            while last_event_count < len(events):
                ev = events[last_event_count]
                yield f"event: progress\ndata: {json.dumps(ev)}\n\n"
                last_event_count += 1

    final_resp = current_state.get("final_response")
    if final_resp:
        yield f"event: final_response\ndata: {json.dumps(final_resp)}\n\n"
    else:
        yield f"event: error\ndata: {json.dumps({'error': 'Workflow produced no final response.'})}\n\n"
