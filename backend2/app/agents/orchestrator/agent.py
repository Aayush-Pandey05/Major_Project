"""
agent.py
========
Orchestrator Agent: Analyzes the natural language query, examines available dataset/source metadata,
and plans the workflow by selecting the necessary specialized agents.
Uses OpenAI if key is configured, or deterministic rule-based planning fallback.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger

class ExecutionPlan(BaseModel):
    intent: str
    target_agents: List[str] # e.g. ['statistical_agent', 'visualization_agent', 'synthesis_agent']
    extracted_params: Dict[str, Any] = Field(default_factory=dict)
    clarification_needed: Optional[str] = None
    reasoning: str

class OrchestratorAgent:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL

    def plan(
        self,
        query: str,
        dataset_meta: Optional[Dict[str, Any]] = None,
        db_connection_url: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        previous_results: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Determines the required agents and parameters for the given user query with multi-turn context."""
        q_lower = query.lower()
        
        # 1. Check if LLM planning is available
        if self.api_key:
            try:
                return self._plan_with_openai(query, dataset_meta, db_connection_url, chat_history, previous_results)
            except Exception as e:
                logger.warning(f"OpenAI planning failed or timed out: {e}. Falling back to deterministic planner.")

        # 2. Deterministic Rule-Based Fallback
        return self._deterministic_plan(q_lower, dataset_meta, db_connection_url, chat_history, previous_results)

    def _deterministic_plan(
        self,
        q_lower: str,
        dataset_meta: Optional[Dict[str, Any]],
        db_connection_url: Optional[str],
        chat_history: Optional[List[Dict[str, Any]]] = None,
        previous_results: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        # Check for visualization requests of previous results (follow-up / cross-question)
        if any(w in q_lower for w in ["visualiz", "plot", "chart", "graph"]) and (
            any(w in q_lower for w in ["this", "it", "previous", "earlier", "result", "above", "now"])
            or not any(w in q_lower for w in ["forecast", "predict", "anomal", "database", "table", "sql", "select"])
        ):
            return ExecutionPlan(
                intent="visualization_followup",
                target_agents=["visualization_agent", "synthesis_agent"],
                extracted_params={},
                reasoning="Follow-up query requesting visualization of the current/previous analytical findings."
            )

        # Check for forecasting
        if any(w in q_lower for w in ["forecast", "predict sales", "future sales", "next 14 days", "next 7 days", "next month", "forecasting"]):
            # Extract horizon
            horizon = 14
            match = re.search(r"(\d+)\s*(days|day)", q_lower)
            if match:
                horizon = min(int(match.group(1)), 90)

            # Extract store number
            store_nbr = 1
            s_match = re.search(r"store\s*(\d+)", q_lower)
            if s_match:
                store_nbr = int(s_match.group(1))

            # Extract family if mentioned
            family = "GROCERY I"
            for fam in ["BEVERAGES", "CLEANING", "DAIRY", "PRODUCE", "BREAD/BAKERY", "POULTRY", "MEATS"]:
                if fam.lower() in q_lower:
                    family = fam
                    break

            return ExecutionPlan(
                intent="forecasting",
                target_agents=["ml_agent", "visualization_agent", "synthesis_agent"],
                extracted_params={
                    "store_nbr": store_nbr,
                    "family": family,
                    "horizon": horizon,
                    "start_date": "2017-08-16"
                },
                reasoning="Query requests future sales predictions. Routed to ML Agent for XGBoost recursive forecasting."
            )

        # Check for anomaly detection
        if any(w in q_lower for w in ["anomal", "unusual", "outlier", "suspicious", "fraud", "irregular", "deviat"]):
            return ExecutionPlan(
                intent="anomaly_detection",
                target_agents=["statistical_agent", "visualization_agent", "synthesis_agent"],
                extracted_params={"top_n": 20, "explain": "flagged"},
                reasoning="Query asks for unusual transactions or outliers. Routed to Statistical Agent for Isolation Forest inference."
            )

        # Check for SQL database query
        if db_connection_url or any(w in q_lower for w in ["database", "sql", "select", "table", "query database"]):
            return ExecutionPlan(
                intent="sql_query",
                target_agents=["sql_agent", "visualization_agent", "synthesis_agent"],
                extracted_params={},
                reasoning="Query relates to external SQL data source. Routed to SQL Agent with read-only validation."
            )

        # Check for summary / correlation / statistics
        if any(w in q_lower for w in ["summarize", "summary", "overview", "describe", "correlation", "distribution", "stats", "statistical"]):
            return ExecutionPlan(
                intent="statistical_summary",
                target_agents=["statistical_agent", "visualization_agent", "synthesis_agent"],
                extracted_params={"mode": "correlation" if "correlation" in q_lower else "summary"},
                reasoning="Query requests dataset profiling or statistical distribution. Routed to Statistical Agent."
            )

        # General inquiry with visualization
        return ExecutionPlan(
            intent="general_analysis",
            target_agents=["statistical_agent", "visualization_agent", "synthesis_agent"],
            extracted_params={},
            reasoning="General analytical query. Routed to Statistical and Visualization agents."
        )

    def _plan_with_openai(
        self,
        query: str,
        dataset_meta: Optional[Dict[str, Any]],
        db_connection_url: Optional[str],
        chat_history: Optional[List[Dict[str, Any]]] = None,
        previous_results: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.0
        )
        meta_str = f"Dataset columns: {dataset_meta.get('columns', [])}" if dataset_meta else "No dataset specified."
        db_str = "External SQL DB connected." if db_connection_url else "No external database connected."

        # Format recent multi-turn conversation history
        history_str = "No prior conversation history."
        if chat_history and len(chat_history) > 0:
            formatted_turns = []
            for m in chat_history[-6:]:
                role = m.get("role", "user").capitalize()
                content = m.get("content", "")[:200]
                formatted_turns.append(f"{role}: {content}")
            history_str = "Recent Conversation History:\n" + "\n".join(formatted_turns)

        prev_results_str = "No previous results."
        if previous_results:
            intent = previous_results.get("plan_intent") or "analysis"
            metrics_keys = list((previous_results.get("metrics") or {}).keys())
            prev_results_str = f"Previous Analysis in this session: Intent='{intent}', Available Metrics={metrics_keys}"

        system_prompt = (
            "You are the Orchestrator Agent in a Multi-Agent AI Data Analyst system.\n"
            "Analyze the user's natural language analytical query in the context of recent conversation history.\n"
            "Support conversational cross-questioning and drill-downs:\n"
            "- If the user asks for a visualization/chart/plot of previous results ('visualize this', 'give me visualization of this result', 'plot it', 'show chart'),\n"
            "  target ['visualization_agent', 'synthesis_agent'] and set 'intent' to 'visualization_followup'.\n"
            "- If the user asks a follow-up question refining previous analysis, preserve previous context/parameters.\n"
            "Available specialized agents:\n"
            "- 'statistical_agent': Isolation Forest anomaly detection, descriptive statistics, correlations.\n"
            "- 'ml_agent': XGBoost time-series retail forecasting.\n"
            "- 'sql_agent': Read-only SQL database querying.\n"
            "- 'visualization_agent': Generating interactive Plotly charts.\n"
            "- 'synthesis_agent': Synthesizing structured evidence into clear narrative findings.\n\n"
            "Output JSON with keys:\n"
            "- 'intent': exactly one of ['forecasting', 'anomaly_detection', 'sql_query', 'statistical_summary', 'visualization_followup', 'general_analysis']\n"
            "- 'target_agents': list of strings\n"
            "- 'extracted_params': object\n"
            "- 'clarification_needed': null or string\n"
            "- 'reasoning': string"
        )

        user_content = f"Query: {query}\nContext:\n{meta_str}\n{db_str}\n{prev_results_str}\n{history_str}"
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
        
        # Parse JSON from response
        import json
        clean_text = response.content.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(clean_text)

        # Normalize intent to match standard intents
        intent_raw = str(data.get("intent", "")).lower()
        if "visualiz" in intent_raw or "chart" in intent_raw or "plot" in intent_raw:
            data["intent"] = "visualization_followup"
            if "visualization_agent" not in data.get("target_agents", []):
                data.setdefault("target_agents", []).append("visualization_agent")
            if "synthesis_agent" not in data.get("target_agents", []):
                data.setdefault("target_agents", []).append("synthesis_agent")
        elif "forecast" in intent_raw or "predict" in intent_raw:
            data["intent"] = "forecasting"
        elif "anomal" in intent_raw or "outlier" in intent_raw or "unusual" in intent_raw:
            data["intent"] = "anomaly_detection"
        elif "sql" in intent_raw or "db" in intent_raw or "table" in intent_raw:
            data["intent"] = "sql_query"
        elif "stat" in intent_raw or "summa" in intent_raw or "corr" in intent_raw:
            data["intent"] = "statistical_summary"

        # Normalize extracted params for downstream deterministic agents
        params = data.setdefault("extracted_params", {})
        if "horizon" not in params or params.get("horizon") is None:
            for k in ["days", "horizon_days", "forecast_days", "period", "n_days"]:
                if k in params:
                    params["horizon"] = int(params[k])
                    break
            if "horizon" not in params:
                match = re.search(r"(\d+)\s*(days|day)", query.lower())
                if match:
                    params["horizon"] = int(match.group(1))

        if "store_nbr" not in params or params.get("store_nbr") is None:
            for k in ["store", "store_id", "store_number"]:
                if k in params:
                    params["store_nbr"] = int(params[k])
                    break
            if "store_nbr" not in params:
                s_match = re.search(r"store\s*(\d+)", query.lower())
                if s_match:
                    params["store_nbr"] = int(s_match.group(1))

        return ExecutionPlan(**data)
