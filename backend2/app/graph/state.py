"""
state.py
========
LangGraph state definitions for the Multi-Agent AI Data Analyst system.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

class AgentState(TypedDict, total=False):
    # Inputs & Conversational Context
    query: str
    session_id: str
    dataset_path: Optional[str]
    dataset_metadata: Optional[Dict[str, Any]]
    db_connection_url: Optional[str]
    chat_history: Optional[List[Dict[str, Any]]]
    previous_results: Optional[Dict[str, Any]]
    
    # Execution Tracking
    current_step: str
    progress_events: List[Dict[str, Any]]
    
    # Orchestrator outputs
    plan_intent: str
    target_agents: List[str]
    extracted_params: Dict[str, Any]
    clarification_needed: Optional[str]
    
    # Specialized agent intermediate artifacts
    statistical_results: Optional[Dict[str, Any]]
    ml_results: Optional[Dict[str, Any]]
    sql_results: Optional[Dict[str, Any]]
    visualization_results: Optional[List[Dict[str, Any]]]
    
    # Final Output
    final_response: Optional[Dict[str, Any]]
    error: Optional[str]
