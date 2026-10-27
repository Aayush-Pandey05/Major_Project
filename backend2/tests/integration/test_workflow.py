"""
test_workflow.py
================
Integration tests for LangGraph multi-agent orchestration.
"""
import pytest
from app.graph.workflow import analyst_graph
from app.graph.state import AgentState

def test_forecasting_workflow_execution():
    initial_state: AgentState = {
        "query": "Forecast sales for the next 7 days for store 1",
        "session_id": "test-session-forecast-01",
        "current_step": "started",
        "progress_events": []
    }

    result = analyst_graph.invoke(initial_state)
    assert result["plan_intent"] == "forecasting"
    assert "ml_agent" in result["target_agents"]
    assert "ml_results" in result
    assert result["ml_results"]["summary_metrics"]["horizon_days"] == 7
    assert len(result["visualization_results"]) >= 1
    assert result["final_response"] is not None
    assert "total_predicted_sales" in result["final_response"]["metrics"]

def test_anomaly_detection_workflow_execution():
    initial_state: AgentState = {
        "query": "Identify unusual transactions and anomalies in this dataset",
        "session_id": "test-session-anom-01",
        "current_step": "started",
        "progress_events": []
    }

    result = analyst_graph.invoke(initial_state)
    assert result["plan_intent"] == "anomaly_detection"
    assert "statistical_agent" in result["target_agents"]
    assert result["final_response"] is not None
