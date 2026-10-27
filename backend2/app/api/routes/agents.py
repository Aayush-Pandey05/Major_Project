"""
agents.py
=========
Orchestrator and specialized agent execution routes for Backend 2.
Supports both synchronous JSON execution and Server-Sent Events (SSE) streaming.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.graph.state import AgentState
from app.graph.workflow import analyst_graph, stream_workflow_events
from app.models.anomaly_detection.service import AnomalyDetectionService
from app.models.anomaly_detection.schemas import AnomalyDetectionRequest, AnomalyDetectionResponse
from app.models.forecasting.service import ForecastingService
from app.models.forecasting.schemas import ForecastingRequest, ForecastingResponse

router = APIRouter(prefix="/agents", tags=["Agents"])

class AgentExecutionRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    dataset_path: Optional[str] = None
    dataset_metadata: Optional[Dict[str, Any]] = None
    db_connection_url: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    previous_results: Optional[Dict[str, Any]] = None

@router.post("/execute")
async def execute_agent_workflow(req: AgentExecutionRequest):
    """Executes the complete LangGraph workflow synchronously."""
    session_id = req.session_id or str(uuid.uuid4())
    initial_state: AgentState = {
        "query": req.query,
        "session_id": session_id,
        "dataset_path": req.dataset_path,
        "dataset_metadata": req.dataset_metadata,
        "db_connection_url": req.db_connection_url,
        "chat_history": req.chat_history or [],
        "previous_results": req.previous_results,
        "current_step": "started",
        "progress_events": []
    }

    try:
        final_state = analyst_graph.invoke(initial_state)
        return {
            "session_id": session_id,
            "query": req.query,
            "plan_intent": final_state.get("plan_intent"),
            "target_agents": final_state.get("target_agents"),
            "progress_events": final_state.get("progress_events", []),
            "response": final_state.get("final_response")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/stream")
async def stream_agent_workflow(req: AgentExecutionRequest):
    """Streams Server-Sent Events (SSE) detailing real agent execution progress and final answer."""
    session_id = req.session_id or str(uuid.uuid4())
    initial_state: AgentState = {
        "query": req.query,
        "session_id": session_id,
        "dataset_path": req.dataset_path,
        "dataset_metadata": req.dataset_metadata,
        "db_connection_url": req.db_connection_url,
        "chat_history": req.chat_history or [],
        "previous_results": req.previous_results,
        "current_step": "started",
        "progress_events": []
    }

    return StreamingResponse(
        stream_workflow_events(initial_state),
        media_type="text/event-stream"
    )

@router.post("/anomaly", response_model=AnomalyDetectionResponse)
async def direct_anomaly_detection(req: AnomalyDetectionRequest):
    service = AnomalyDetectionService()
    if not req.dataset_path:
        raise HTTPException(status_code=400, detail="dataset_path is required.")
    try:
        return service.detect_anomalies(
            data=req.dataset_path,
            explain=req.explain,
            top_n=req.top_n,
            contamination=req.contamination
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Anomaly detection failed: {str(e)}")

@router.post("/forecast", response_model=ForecastingResponse)
async def direct_forecasting(req: ForecastingRequest):
    service = ForecastingService()
    try:
        return service.forecast_sales(
            store_nbr=req.store_nbr,
            family=req.family,
            start_date=req.start_date,
            horizon=req.horizon,
            dataset_path=req.dataset_path,
            date_column=req.date_column,
            target_column=req.target_column
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Forecasting failed: {str(e)}")
