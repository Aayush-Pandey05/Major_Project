"""
service.py
==========
High-level service orchestrating time-series sales forecasting.
Operates on separate in-memory data copies, strictly never modifies source files,
and exports forecasts as separate result files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union
import uuid
from datetime import datetime

import pandas as pd

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import DataValidationError
from app.models.forecasting.inference import StoreSalesForecaster, GenericTimeSeriesForecaster
from app.models.forecasting.schemas import ForecastingResponse, ForecastPoint

class ForecastingService:
    def __init__(self):
        self._forecaster: Optional[StoreSalesForecaster] = None

    def _get_forecaster(self) -> StoreSalesForecaster:
        if self._forecaster is None:
            self._forecaster = StoreSalesForecaster()
        return self._forecaster

    def forecast_sales(
        self,
        store_nbr: int = 1,
        family: str = "GROCERY I",
        start_date: str = "2017-08-16",
        horizon: int = 16,
        dataset_path: Optional[str] = None,
        date_column: Optional[str] = "date",
        target_column: Optional[str] = "sales",
    ) -> ForecastingResponse:
        forecaster = self._get_forecaster()
        custom_history: Optional[pd.DataFrame] = None
        warning: Optional[str] = None

        if dataset_path:
            p = Path(dataset_path)
            if not p.exists():
                raise DataValidationError(f"Dataset path not found: {p}")
            if p.suffix.lower() == ".csv":
                df = pd.read_csv(p)
            elif p.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(p)
            else:
                raise DataValidationError(f"Unsupported format: {p.suffix}")

            # Check if columns match store sales or generic time series
            cols_lower = [c.lower() for c in df.columns]
            if "store_nbr" in cols_lower and "family" in cols_lower and "sales" in cols_lower:
                logger.info("Uploaded dataset matches store sales format.")
                # Filter for specific series
                df_clean = df.rename(columns={c: c.lower() for c in df.columns})
                custom_history = df_clean[
                    (df_clean['store_nbr'] == store_nbr) &
                    (df_clean['family'].str.upper() == family.upper())
                ].copy()
            elif date_column and target_column and date_column in df.columns and target_column in df.columns:
                logger.info("Using generic time series forecaster for uploaded dataset.")
                generic = GenericTimeSeriesForecaster()
                res_df = generic.forecast(df, date_col=date_column, target_col=target_column, horizon=horizon)
                warning = "Generated using generic time-series forecaster on uploaded target series."
                
                # Format response
                export_filename = f"forecast_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.csv"
                export_path = settings.RESULTS_DIR / export_filename
                res_df.to_csv(export_path, index=False)
                
                points = [ForecastPoint(**row) for row in res_df.to_dict(orient="records")]
                return ForecastingResponse(
                    model_name="Generic Time-Series Forecaster",
                    model_version="1.0.0",
                    forecast_strategy="Recursive Lag Regression",
                    horizon_days=horizon,
                    store_nbr=None,
                    family=None,
                    start_date=res_df.iloc[0]['date'],
                    end_date=res_df.iloc[-1]['date'],
                    forecasts=points,
                    historical_summary={"points_provided": len(df)},
                    evaluation_benchmarks={},
                    export_file_url=f"/api/v1/results/download/{export_filename}",
                    warning=warning
                )

        # Standard pre-trained XGBoost retail forecasting
        res_df = forecaster.forecast_single_series(
            store_nbr=store_nbr,
            family=family,
            start_date=start_date,
            horizon=horizon,
            custom_history=custom_history
        )

        export_filename = f"forecast_store_{store_nbr}_{family.replace('/', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.csv"
        export_path = settings.RESULTS_DIR / export_filename
        res_df.to_csv(export_path, index=False)
        logger.info(f"Forecast saved separately to {export_path}")

        points = [ForecastPoint(**row) for row in res_df.to_dict(orient="records")]
        benchmarks = forecaster.metadata.get("evaluation_metrics", {})

        return ForecastingResponse(
            model_name="XGBoost Time-Series Sales Forecaster",
            model_version=forecaster.model_version,
            forecast_strategy="Recursive Multi-Step Forecasting (Lags 1, 7, 14, 28 and Shifted Rolling Stats)",
            horizon_days=horizon,
            store_nbr=store_nbr,
            family=family,
            start_date=res_df.iloc[0]['date'],
            end_date=res_df.iloc[-1]['date'],
            forecasts=points,
            historical_summary={
                "mean_forecast_sales": round(float(res_df['predicted_sales'].mean()), 2),
                "total_forecast_sales": round(float(res_df['predicted_sales'].sum()), 2),
                "peak_sales_day": res_df.loc[res_df['predicted_sales'].idxmax()]['date'],
                "peak_sales_value": round(float(res_df['predicted_sales'].max()), 2)
            },
            evaluation_benchmarks=benchmarks,
            export_file_url=f"/api/v1/results/download/{export_filename}",
            warning=warning
        )
