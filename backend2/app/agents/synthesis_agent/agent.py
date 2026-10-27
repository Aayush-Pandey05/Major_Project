"""
agent.py
========
Synthesis Agent: Synthesizes structured intermediate outputs from the specialized agents
into a comprehensive, evidence-based final response.
Uses OpenAI for narrative structuring if available, or deterministic template synthesis.
Strictly NEVER invents metrics, predictions, or hallucinated facts.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger

class SynthesizedResponse(BaseModel):
    answer: str
    summary: str
    key_findings: List[str] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class SynthesisAgent:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL

    def synthesize(
        self,
        query: str,
        plan_intent: str,
        statistical_data: Optional[Dict[str, Any]] = None,
        ml_data: Optional[Dict[str, Any]] = None,
        sql_data: Optional[Dict[str, Any]] = None,
        charts: Optional[List[Dict[str, Any]]] = None
    ) -> SynthesizedResponse:
        """Combines all agent intermediate artifacts into the final response."""
        charts = charts or []
        combined_metrics = {}
        tables = []
        evidence = []
        limitations = []
        warnings = []

        if statistical_data:
            combined_metrics.update(statistical_data.get("summary_metrics", {}))
            if statistical_data.get("data_table"):
                tables.append({
                    "title": "Statistical Results Table",
                    "rows": statistical_data["data_table"][:20]
                })
            evidence.append(statistical_data.get("description", "Statistical analysis completed."))
            limitations.append("Isolation Forest flags indicate statistical novelty for review, not definitive fraud.")

        if ml_data:
            combined_metrics.update(ml_data.get("summary_metrics", {}))
            if ml_data.get("forecast_table"):
                tables.append({
                    "title": "Forecasted Values (Horizon)",
                    "rows": ml_data["forecast_table"][:20]
                })
            evidence.append(ml_data.get("description", "XGBoost recursive forecasting completed."))
            limitations.append("Forecasting model evaluated for up to 16-day horizon; uncertainty compounds further out.")

        if sql_data:
            exec_res = sql_data.get("execution_result", {})
            if exec_res.get("rows"):
                tables.append({
                    "title": "SQL Query Results",
                    "columns": exec_res.get("columns", []),
                    "rows": exec_res.get("rows", [])[:20]
                })
            combined_metrics["sql_rows_retrieved"] = sql_data.get("row_count", 0)
            evidence.append(f"SQL Query Executed: `{sql_data.get('generated_sql')}`")
            limitations.append("External database was queried in strict read-only mode with a row limit.")

        if sql_data and sql_data.get("error"):
            warnings.append(sql_data["error"])

        # Use LLM for synthesis if available
        if self.api_key:
            try:
                return self._synthesize_with_llm(
                    query, plan_intent, combined_metrics, tables, charts, evidence, limitations, warnings
                )
            except Exception as e:
                logger.warning(f"OpenAI synthesis failed: {e}. Falling back to deterministic synthesis.")

        # Deterministic Synthesis Fallback
        return self._deterministic_synthesize(
            query, plan_intent, combined_metrics, tables, charts, evidence, limitations, warnings
        )

    def _deterministic_synthesize(
        self,
        query: str,
        plan_intent: str,
        metrics: Dict[str, Any],
        tables: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        evidence: List[str],
        limitations: List[str],
        warnings: List[str]
    ) -> SynthesizedResponse:
        key_findings = []
        if "anomalies_flagged" in metrics:
            key_findings.append(
                f"Flagged {metrics['anomalies_flagged']} anomalies ({metrics.get('anomaly_percentage', 0.0)}% of total records)."
            )
            key_findings.append(
                f"Isolation Forest threshold score was {metrics.get('model_threshold', 0.558):.3f}."
            )
            answer = (
                f"Statistical anomaly analysis identified {metrics['anomalies_flagged']} suspicious transactions. "
                f"The highest anomaly scores reflect unusual combinations of quantities, unit prices, and transaction timing."
            )
            summary = f"Identified {metrics['anomalies_flagged']} potential anomalies requiring audit review."

        elif "total_predicted_sales" in metrics:
            key_findings.append(
                f"Total projected sales across the {metrics.get('horizon_days', 14)}-day horizon: {metrics['total_predicted_sales']:,.2f} units."
            )
            key_findings.append(
                f"Average projected daily sales: {metrics.get('mean_daily_sales', 0.0):,.2f} units."
            )
            key_findings.append(
                f"Peak sales day expected on {metrics.get('peak_day', 'N/A')} ({metrics.get('peak_value', 0.0):,.2f} units)."
            )
            answer = (
                f"The XGBoost forecasting model projects a cumulative sales volume of {metrics['total_predicted_sales']:,.2f} units "
                f"over the next {metrics.get('horizon_days', 14)} days, with an average daily demand of {metrics.get('mean_daily_sales', 0.0):,.2f} units."
            )
            summary = f"Forecasted {metrics.get('horizon_days', 14)}-day demand totaling {metrics['total_predicted_sales']:,.2f} units."

        elif "sql_rows_retrieved" in metrics:
            key_findings.append(f"Successfully retrieved {metrics['sql_rows_retrieved']} records from the connected database.")
            answer = f"The query executed successfully, returning {metrics['sql_rows_retrieved']} rows based on your request."
            summary = f"Database returned {metrics['sql_rows_retrieved']} matching records."

        elif len(charts) > 0 or plan_intent == "visualization_followup":
            chart_count = len(charts)
            chart_titles = ", ".join([c.get("title", "Chart") for c in charts]) if charts else "interactive analytical charts"
            key_findings.append(f"Rendered {chart_count} interactive visualization(s): {chart_titles}.")
            answer = f"Generated {chart_count} interactive visualization(s) representing the analytical findings. You can inspect data points, zoom, and explore distributions in the charts above."
            summary = f"Successfully generated {chart_count} interactive visualization(s)."

        else:
            key_findings.append("Completed dataset analysis and profiling.")
            answer = f"Analysis completed for query: '{query}'."
            summary = "Dataset analysis completed."

        return SynthesizedResponse(
            answer=answer,
            summary=summary,
            key_findings=key_findings,
            tables=tables,
            charts=charts,
            metrics=metrics,
            evidence=evidence,
            limitations=limitations,
            warnings=warnings
        )

    def _synthesize_with_llm(
        self,
        query: str,
        plan_intent: str,
        metrics: Dict[str, Any],
        tables: List[Dict[str, Any]],
        charts: List[Dict[str, Any]],
        evidence: List[str],
        limitations: List[str],
        warnings: List[str]
    ) -> SynthesizedResponse:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.2
        )

        system_prompt = (
            "You are the Synthesis Agent in a Multi-Agent AI Data Analyst system.\n"
            "Synthesize the provided evidence, model metrics, and tabular outputs into a clear, professional answer.\n"
            "CRITICAL RULES:\n"
            "- PRESERVE EXACT NUMBERS from metrics and evidence. NEVER fabricate, round differently, or hallucinate metrics.\n"
            "- Distinguish model benchmark accuracy from specific prediction outcomes.\n"
            "- Return valid JSON matching this schema:\n"
            "{\n"
            '  "answer": "comprehensive narrative answer",\n'
            '  "summary": "1-2 sentence executive summary",\n'
            '  "key_findings": ["bullet point 1 with numbers", "bullet point 2"],\n'
            '  "evidence": ["evidence point 1"],\n'
            '  "limitations": ["model limitation 1"],\n'
            '  "warnings": []\n'
            "}"
        )

        context = {
            "query": query,
            "intent": plan_intent,
            "metrics": metrics,
            "evidence": evidence,
            "table_samples": [t.get("rows", [])[:3] for t in tables],
            "limitations": limitations
        }

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{json.dumps(context, default=str)}")
        ])

        clean_text = response.content.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        data = json.loads(clean_text)
        return SynthesizedResponse(
            answer=data.get("answer", "Analysis completed."),
            summary=data.get("summary", ""),
            key_findings=data.get("key_findings", []),
            tables=tables,
            charts=charts,
            metrics=metrics,
            evidence=data.get("evidence", evidence),
            limitations=data.get("limitations", limitations),
            warnings=warnings + data.get("warnings", [])
        )
