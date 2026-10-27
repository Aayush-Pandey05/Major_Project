"""
schemas.py
==========
Pydantic schemas for time-series sales forecasting inputs, results, and metrics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ForecastPoint(BaseModel):
    date: str
    predicted_sales: float
    store_nbr: Optional[int] = None
    family: Optional[str] = None
    forecast_horizon_day: int
    dayofweek: int
    onpromotion: float = 0.0
    is_holiday: int = 0
    oil_price: Optional[float] = None

class ForecastEvaluationMetrics(BaseModel):
    RMSLE: float
    MAE: float
    RMSE: float
    WAPE_percent: float = Field(alias="WAPE (%)", default=0.0)

class ForecastingRequest(BaseModel):
    dataset_path: Optional[str] = None
    store_nbr: int = 1
    family: str = "GROCERY I"
    start_date: str = "2017-08-16"
    horizon: int = 16
    target_column: Optional[str] = "sales"
    date_column: Optional[str] = "date"

class ForecastingResponse(BaseModel):
    model_name: str = "XGBoost Time-Series Sales Forecaster"
    model_version: str = "1.0.0"
    forecast_strategy: str = "Recursive Multi-Step Forecasting (Lags 1, 7, 14, 28 and Shifted Rolling Stats)"
    horizon_days: int
    store_nbr: Optional[int] = None
    family: Optional[str] = None
    start_date: str
    end_date: str
    forecasts: List[ForecastPoint]
    historical_summary: Dict[str, Any] = Field(default_factory=dict)
    evaluation_benchmarks: Dict[str, Any] = Field(default_factory=dict)
    export_file_url: Optional[str] = None
    warning: Optional[str] = None
