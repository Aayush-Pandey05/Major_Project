"""
nodes.py
========
Execution nodes for LangGraph orchestrator.
Each node updates the state and logs real progress events.
"""
from __future__ import annotations

import time
from typing import Any, Dict
from app.core.logging import logger
from app.graph.state import AgentState
from app.agents.orchestrator.agent import OrchestratorAgent
from app.agents.statistical_agent.agent import StatisticalAgent
from app.agents.ml_agent.agent import MLAgent
from app.agents.sql_agent.agent import SQLAgent
from app.agents.visualization_agent.agent import VisualizationAgent
from app.agents.synthesis_agent.agent import SynthesisAgent

def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Orchestrator Node...")
    agent = OrchestratorAgent()
    plan = agent.plan(
        query=state["query"],
        dataset_meta=state.get("dataset_metadata"),
        db_connection_url=state.get("db_connection_url"),
        chat_history=state.get("chat_history"),
        previous_results=state.get("previous_results")
    )
    
    event = {
        "step": "orchestrator",
        "agent": "Orchestrator Agent",
        "status": "planned",
        "message": f"Identified intent: '{plan.intent}'. Selected workflow: {', '.join(plan.target_agents)}.",
        "timestamp": time.time()
    }
    
    events = list(state.get("progress_events", []))
    events.append(event)
    
    return {
        "current_step": "orchestrated",
        "plan_intent": plan.intent,
        "target_agents": plan.target_agents,
        "extracted_params": plan.extracted_params,
        "clarification_needed": plan.clarification_needed,
        "progress_events": events
    }

def statistical_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Statistical Node...")
    agent = StatisticalAgent()
    intent = state.get("plan_intent", "anomaly_detection")
    params = state.get("extracted_params", {})
    
    task = "anomaly_detection" if "anomal" in intent or intent == "anomaly_detection" else "correlation" if intent == "correlation" else "descriptive_summary"
    data_source = state.get("dataset_path")
    
    # If no dataset_path provided, check if sample/reference exists
    if not data_source:
        # Default to small sample or raise
        from app.core.config import settings
        # Look in artifacts or sample
        data_source = settings.MODEL_ARTIFACTS_DIR / "sample.csv" # placeholder if needed
    
    try:
        res = agent.run_analysis(data=data_source, task=task, params=params)
        res_dict = res.model_dump()
        msg = res.description
    except Exception as e:
        logger.error(f"Statistical node error: {e}")
        res_dict = {"error": str(e), "summary_metrics": {}}
        msg = f"Statistical analysis notice: {str(e)}"

    event = {
        "step": "statistical_agent",
        "agent": "Statistical Agent",
        "status": "completed",
        "message": msg,
        "timestamp": time.time()
    }
    events = list(state.get("progress_events", []))
    events.append(event)

    return {
        "current_step": "statistical_completed",
        "statistical_results": res_dict,
        "progress_events": events
    }

def ml_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing ML Forecasting Node...")
    agent = MLAgent()
    params = state.get("extracted_params", {})
    
    store_nbr = params.get("store_nbr", 1)
    family = params.get("family", "GROCERY I")
    horizon = params.get("horizon", 14)
    start_date = params.get("start_date", "2017-08-16")
    dataset_path = state.get("dataset_path")

    try:
        res = agent.run_forecast(
            store_nbr=store_nbr,
            family=family,
            start_date=start_date,
            horizon=horizon,
            dataset_path=dataset_path
        )
        res_dict = res.model_dump()
        msg = res.description
    except Exception as e:
        logger.error(f"ML node error: {e}")
        res_dict = {"error": str(e), "summary_metrics": {}, "forecast_table": []}
        msg = f"Forecasting notice: {str(e)}"

    event = {
        "step": "ml_agent",
        "agent": "ML Agent (XGBoost)",
        "status": "completed",
        "message": msg,
        "timestamp": time.time()
    }
    events = list(state.get("progress_events", []))
    events.append(event)

    return {
        "current_step": "ml_completed",
        "ml_results": res_dict,
        "progress_events": events
    }

def sql_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing SQL Agent Node...")
    agent = SQLAgent()
    conn_url = state.get("db_connection_url")
    
    if not conn_url:
        res_dict = {"error": "No database connection configured for SQL Agent."}
        msg = "SQL Agent: No external database connection supplied."
    else:
        res = agent.execute_query(
            query=state["query"],
            connection_url=conn_url,
            schema_metadata=state.get("dataset_metadata")
        )
        res_dict = res.model_dump()
        msg = res.explanation or res.error or "SQL execution finished."

    event = {
        "step": "sql_agent",
        "agent": "SQL Agent",
        "status": "completed",
        "message": msg,
        "timestamp": time.time()
    }
    events = list(state.get("progress_events", []))
    events.append(event)

    return {
        "current_step": "sql_completed",
        "sql_results": res_dict,
        "progress_events": events
    }

def visualization_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Visualization Node...")
    agent = VisualizationAgent()
    charts = []
    prev_res = state.get("previous_results") or {}

    # 1. Check for ML forecasting records (Current turn or Previous conversational results)
    ml_res = state.get("ml_results") or {}
    forecast_table = ml_res.get("forecast_table")
    if not forecast_table and prev_res.get("tables"):
        for t in prev_res["tables"]:
            if any(k in t.get("title", "").lower() for k in ["forecast", "sales", "predicted"]) and t.get("rows"):
                forecast_table = t["rows"]
                break

    if forecast_table:
        try:
            c = agent.create_forecast_chart(forecast_table)
            charts.append(c.model_dump())
        except Exception as e:
            logger.warning(f"Failed to generate forecast chart: {e}")

    # 2. Check for Anomaly detection records (Current turn or Previous conversational results)
    stat_res = state.get("statistical_results") or {}
    anom_res = stat_res.get("anomaly_response")
    flagged_records = None
    threshold = 0.558

    if anom_res and anom_res.get("flagged_records"):
        flagged_records = anom_res["flagged_records"]
        threshold = float(anom_res.get("threshold_score", 0.558))
    elif prev_res.get("tables"):
        for t in prev_res["tables"]:
            rows = t.get("rows", [])
            if rows and any("anomaly" in str(k).lower() for k in rows[0].keys()):
                flagged_records = rows
                threshold = float(prev_res.get("metrics", {}).get("model_threshold", 0.558))
                break

    if flagged_records:
        try:
            c = agent.create_anomaly_scatter_chart(flagged_records, threshold=threshold)
            charts.append(c.model_dump())
        except Exception as e:
            logger.warning(f"Failed to generate anomaly scatter chart: {e}")
    elif stat_res.get("correlation_matrix"):
        try:
            c = agent.create_correlation_heatmap(stat_res["correlation_matrix"])
            charts.append(c.model_dump())
        except Exception as e:
            logger.warning(f"Failed to generate correlation heatmap: {e}")

    # 3. Check for SQL database results (Current turn or Previous conversational results)
    sql_res = state.get("sql_results") or {}
    exec_res = sql_res.get("execution_result", {})
    sql_rows = exec_res.get("rows")
    sql_cols = exec_res.get("columns", [])
    if not sql_rows and prev_res.get("tables"):
        for t in prev_res["tables"]:
            if "sql" in t.get("title", "").lower() and t.get("rows") and t.get("columns"):
                sql_rows = t["rows"]
                sql_cols = t["columns"]
                break

    if sql_rows and len(sql_cols) >= 2:
        col0 = sql_cols[0]
        col1 = sql_cols[1]
        try:
            cats = [str(r[col0]) for r in sql_rows[:15]]
            vals = [float(r[col1]) for r in sql_rows[:15]]
            c = agent.create_bar_chart(cats, vals, title=f"{col1} by {col0}", x_label=col0, y_label=col1)
            charts.append(c.model_dump())
        except Exception as e:
            logger.debug(f"SQL bar chart not applicable: {e}")

    # 4. Fallback Chart: Key Analytical Metrics Overview Bar Chart
    if not charts:
        metrics = stat_res.get("summary_metrics") or ml_res.get("summary_metrics") or prev_res.get("metrics")
        if metrics and isinstance(metrics, dict) and any(isinstance(v, (int, float)) for v in metrics.values()):
            try:
                c = agent.create_metrics_summary_chart(metrics)
                charts.append(c.model_dump())
            except Exception as e:
                logger.debug(f"Metrics bar chart not created: {e}")

    # 5. Fallback Chart: Distribution of primary numerical column from uploaded dataset
    if not charts and state.get("dataset_path"):
        try:
            from app.services.csv_excel.loader import DatasetLoader
            df, _ = DatasetLoader.load_dataset(state["dataset_path"])
            num_cols = df.select_dtypes(include=["number"]).columns.tolist()
            if num_cols:
                primary_col = num_cols[0]
                values = df[primary_col].dropna().tolist()[:1000]
                if values:
                    c = agent.create_distribution_chart(values, column_name=primary_col)
                    charts.append(c.model_dump())
        except Exception as e:
            logger.debug(f"Dataset distribution chart not created: {e}")

    event = {
        "step": "visualization_agent",
        "agent": "Visualization Agent (Plotly)",
        "status": "completed",
        "message": f"Generated {len(charts)} interactive chart(s).",
        "timestamp": time.time()
    }
    events = list(state.get("progress_events", []))
    events.append(event)

    return {
        "current_step": "visualization_completed",
        "visualization_results": charts,
        "progress_events": events
    }

def synthesis_node(state: AgentState) -> Dict[str, Any]:
    logger.info("Executing Synthesis Node...")
    agent = SynthesisAgent()
    
    synth = agent.synthesize(
        query=state["query"],
        plan_intent=state.get("plan_intent", "general"),
        statistical_data=state.get("statistical_results"),
        ml_data=state.get("ml_results"),
        sql_data=state.get("sql_results"),
        charts=state.get("visualization_results")
    )

    event = {
        "step": "synthesis_agent",
        "agent": "Synthesis Agent",
        "status": "completed",
        "message": "Synthesized final evidence-based response with key findings and charts.",
        "timestamp": time.time()
    }
    events = list(state.get("progress_events", []))
    events.append(event)

    return {
        "current_step": "completed",
        "final_response": synth.model_dump(),
        "progress_events": events
    }
