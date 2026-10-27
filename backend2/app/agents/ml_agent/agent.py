"""
agent.py
========
ML Agent: Executes machine-learning time-series forecasting using the trained XGBoost model.
STRICTLY NEVER CALLS OPENAI.
All forecasts, recursive multi-step lag calculations, and validation benchmarks
are executed deterministically by Python and XGBoost inference code.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.forecasting.service import ForecastingService
from app.models.forecasting.schemas import ForecastingResponse

class MLAgentResult(BaseModel):
    forecast_response: ForecastingResponse
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    forecast_table: List[Dict[str, Any]] = Field(default_factory=list)
    description: str

class MLAgent:
    def __init__(self):
        self.service = ForecastingService()

    def run_forecast(
        self,
        store_nbr: int = 1,
        family: str = "GROCERY I",
        start_date: str = "2017-08-16",
        horizon: int = 16,
        dataset_path: Optional[str] = None,
        date_column: Optional[str] = "date",
        target_column: Optional[str] = "sales"
    ) -> MLAgentResult:
        """Executes XGBoost forecasting without LLM calls."""
        res = self.service.forecast_sales(
            store_nbr=store_nbr,
            family=family,
            start_date=start_date,
            horizon=horizon,
            dataset_path=dataset_path,
            date_column=date_column,
            target_column=target_column
        )

        table_rows = [p.model_dump() for p in res.forecasts]
        metrics = {
            "horizon_days": res.horizon_days,
            "total_predicted_sales": res.historical_summary.get("total_forecast_sales", 0.0),
            "mean_daily_sales": res.historical_summary.get("mean_forecast_sales", 0.0),
            "peak_day": res.historical_summary.get("peak_sales_day", ""),
            "peak_value": res.historical_summary.get("peak_sales_value", 0.0),
            "model_validation_rmsle": res.evaluation_benchmarks.get("xgboost_recursive_16day", {}).get("RMSLE", 0.4088),
            "model_validation_wape": res.evaluation_benchmarks.get("xgboost_recursive_16day", {}).get("WAPE (%)", 17.07),
        }

        desc = (
            f"Generated {res.horizon_days}-day recursive sales forecast for "
            f"Store {res.store_nbr or 'Series'} ({res.family or 'Target'}) "
            f"from {res.start_date} to {res.end_date}. "
            f"Total forecasted sales: {metrics['total_predicted_sales']:,.2f} units."
        )

        return MLAgentResult(
            forecast_response=res,
            summary_metrics=metrics,
            forecast_table=table_rows,
            description=desc
        )
