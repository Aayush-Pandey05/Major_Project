"""
inference.py
------------
Inference forecaster that loads the pre-trained XGBoost model and fitted categorical
mappings without retraining. Executes recursive multi-step forecasting.
Also provides a generic time-series forecaster fallback for arbitrary datasets.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ModelInferenceError, DataValidationError
from app.models.forecasting.feature_engineering import (
    add_calendar_features,
    preprocess_oil_data,
    preprocess_holiday_data,
    compute_step_lags_and_rolling,
    FEATURE_COLUMNS
)

DEFAULT_XGB_ARTIFACT = settings.MODEL_ARTIFACTS_DIR / "xgboost_sales_forecasting_model.joblib"
DEFAULT_XGB_METADATA = settings.MODEL_ARTIFACTS_DIR / "xgboost_metadata.json"
DEFAULT_REF_DIR = settings.FORECAST_REF_DIR

class StoreSalesForecaster:
    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        metadata_path: Optional[Union[str, Path]] = None,
        data_dir: Optional[Union[str, Path]] = None
    ):
        m_path = Path(model_path) if model_path else DEFAULT_XGB_ARTIFACT
        if not m_path.exists():
            raise ModelInferenceError(f"Forecasting model artifact not found at: {m_path}")

        try:
            self.artifact = joblib.load(m_path)
        except Exception as e:
            raise ModelInferenceError(f"Failed to load XGBoost artifact: {e}") from e

        self.model = self.artifact['model']
        self.feature_columns = self.artifact.get('feature_columns', FEATURE_COLUMNS)
        self.categorical_mappings = self.artifact['categorical_mappings']
        self.model_version = self.artifact.get('model_version', '1.0.0')

        self.valid_stores = set(self.categorical_mappings['store_nbr'].keys())
        self.valid_families = set(self.categorical_mappings['family'].keys())
        self.inv_store_map = {v: k for k, v in self.categorical_mappings['store_nbr'].items()}
        self.inv_family_map = {v: k for k, v in self.categorical_mappings['family'].items()}

        meta_p = Path(metadata_path) if metadata_path else DEFAULT_XGB_METADATA
        self.metadata = {}
        if meta_p.exists():
            with open(meta_p, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

        self.data_dir = Path(data_dir) if data_dir else DEFAULT_REF_DIR
        self._stores_meta = None
        self._raw_oil = None
        self._raw_holidays = None
        self._reference_history = None

        self._load_support_data()

    def _load_support_data(self):
        stores_file = self.data_dir / "stores.csv"
        oil_file = self.data_dir / "oil.csv"
        holidays_file = self.data_dir / "holidays_events.csv"
        history_parquet = self.data_dir / "reference_history.parquet"

        if not (stores_file.exists() and oil_file.exists() and holidays_file.exists()):
            raise ModelInferenceError(f"Missing support data in {self.data_dir}")

        self._stores_meta = pd.read_csv(stores_file)
        self._raw_oil = pd.read_csv(oil_file)
        self._raw_oil['date'] = pd.to_datetime(self._raw_oil['date'])
        self._raw_holidays = pd.read_csv(holidays_file)
        self._raw_holidays['date'] = pd.to_datetime(self._raw_holidays['date'])

        if history_parquet.exists():
            self._reference_history = pd.read_parquet(history_parquet)
            self._reference_history['date'] = pd.to_datetime(self._reference_history['date'])

    def _get_history(self, store_nbr: int, family: str) -> pd.DataFrame:
        if self._reference_history is None:
            raise ModelInferenceError("No historical sales reference available.")
        
        series_df = self._reference_history[
            (self._reference_history['store_nbr'] == store_nbr) &
            (self._reference_history['family'] == family)
        ].sort_values('date').copy()
        return series_df

    def validate_inputs(
        self,
        store_nbr: int,
        family: str,
        start_date: Union[str, datetime, pd.Timestamp],
        horizon: int
    ) -> Tuple[int, str, pd.Timestamp, int]:
        try:
            store_nbr = int(store_nbr)
        except (ValueError, TypeError):
            raise DataValidationError(f"Invalid store_nbr '{store_nbr}'. Must be an integer.")

        if store_nbr not in self.valid_stores:
            raise DataValidationError(
                f"Unknown store_nbr: {store_nbr}. Valid stores: {sorted(list(self.valid_stores))[:10]}..."
            )

        family_clean = str(family).strip().upper().replace('_', '/')
        if family_clean not in self.valid_families:
            matching = [f for f in self.valid_families if f.upper() == family_clean.upper()]
            if matching:
                family_clean = matching[0]
            else:
                raise DataValidationError(
                    f"Unknown product family '{family}'. Valid families: {sorted(list(self.valid_families))}"
                )

        try:
            horizon = int(horizon)
        except (ValueError, TypeError):
            raise DataValidationError(f"Invalid horizon '{horizon}'.")

        if horizon <= 0:
            raise DataValidationError(f"Horizon must be at least 1 day, got {horizon}.")
        if horizon > 90:
            raise DataValidationError(f"Horizon cannot exceed 90 days, got {horizon}.")

        try:
            start_date_ts = pd.to_datetime(start_date)
        except Exception as e:
            raise DataValidationError(f"Invalid start_date '{start_date}': {e}")

        return store_nbr, family_clean, start_date_ts, horizon

    def forecast_single_series(
        self,
        store_nbr: int = 1,
        family: str = "GROCERY I",
        start_date: Union[str, datetime, pd.Timestamp] = "2017-08-16",
        horizon: int = 16,
        future_promotions: Optional[Dict[str, float]] = None,
        custom_history: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        store_nbr, family, start_date_ts, horizon = self.validate_inputs(store_nbr, family, start_date, horizon)

        if custom_history is not None:
            hist_df = custom_history.copy()
            hist_df['date'] = pd.to_datetime(hist_df['date'])
            hist_df = hist_df.sort_values('date')
        else:
            hist_df = self._get_history(store_nbr, family)

        hist_df = hist_df[hist_df['date'] < start_date_ts].copy()
        if len(hist_df) < 28:
            raise DataValidationError(
                f"Requires at least 28 historical days for Store {store_nbr}, Family '{family}', found {len(hist_df)}."
            )

        full_hist_dates = pd.date_range(hist_df['date'].min(), start_date_ts - timedelta(days=1))
        hist_grid = pd.DataFrame({'date': full_hist_dates})
        hist_df = pd.merge(hist_grid, hist_df, on='date', how='left')
        hist_df['sales'] = hist_df['sales'].fillna(0.0)
        hist_df['onpromotion'] = hist_df.get('onpromotion', pd.Series(0.0, index=hist_df.index)).fillna(0.0)

        history_sales = list(hist_df['sales'].values)
        forecast_dates = pd.date_range(start_date_ts, periods=horizon, freq='D')

        # External covariates
        full_ext_range = pd.date_range(hist_df['date'].min(), forecast_dates[-1], freq='D')
        oil_features = preprocess_oil_data(self._raw_oil, full_ext_range)
        holiday_features = preprocess_holiday_data(self._raw_holidays, full_ext_range)

        # Store metadata
        store_row = self._stores_meta[self._stores_meta['store_nbr'] == store_nbr].iloc[0]
        store_city = store_row['city']
        store_state = store_row['state']
        store_type = store_row['type']
        store_cluster = store_row['cluster']

        store_code = self.categorical_mappings['store_nbr'][store_nbr]
        family_code = self.categorical_mappings['family'][family]
        city_code = self.categorical_mappings['city'].get(store_city, 0)
        state_code = self.categorical_mappings['state'].get(store_state, 0)
        type_code = self.categorical_mappings['type'].get(store_type, 0)
        cluster_code = self.categorical_mappings['cluster'].get(store_cluster, 0)

        forecast_records = []
        for step_idx, cur_date in enumerate(forecast_dates):
            date_str = cur_date.strftime('%Y-%m-%d')
            lag_roll_features = compute_step_lags_and_rolling(history_sales)

            cal_features = {
                'year': cur_date.year,
                'month': cur_date.month,
                'day': cur_date.day,
                'dayofweek': cur_date.dayofweek,
                'dayofyear': cur_date.dayofyear,
                'weekofyear': int(cur_date.isocalendar().week),
                'is_weekend': 1 if cur_date.dayofweek >= 5 else 0,
            }

            oil_row = oil_features[oil_features['date'] == cur_date]
            oil_price = float(oil_row['dcoilwtico'].values[0]) if not oil_row.empty else 47.0
            oil_lag_1 = float(oil_row['oil_lag_1'].values[0]) if not oil_row.empty else oil_price
            oil_roll_7 = float(oil_row['oil_rolling_mean_7'].values[0]) if not oil_row.empty else oil_price

            hol_row = holiday_features[holiday_features['date'] == cur_date]
            is_hol = int(hol_row['is_holiday'].values[0]) if not hol_row.empty else 0
            is_nat_hol = int(hol_row['is_national_holiday'].values[0]) if not hol_row.empty else 0
            is_workday = int(hol_row['is_workday'].values[0]) if not hol_row.empty else 0

            promo_val = 0.0
            if future_promotions and date_str in future_promotions:
                promo_val = float(future_promotions[date_str])

            row_dict = {
                'store_nbr': store_code,
                'family': family_code,
                'type': type_code,
                'cluster': cluster_code,
                'city': city_code,
                'state': state_code,
                'onpromotion': promo_val,
                'dcoilwtico': oil_price,
                'oil_lag_1': oil_lag_1,
                'oil_rolling_mean_7': oil_roll_7,
                'is_holiday': is_hol,
                'is_national_holiday': is_nat_hol,
                'is_workday': is_workday,
                **cal_features,
                **lag_roll_features
            }

            X_step = pd.DataFrame([row_dict])[self.feature_columns]
            pred_log1p = self.model.predict(X_step)[0]
            pred_sales = float(np.clip(np.expm1(pred_log1p), 0, None))

            history_sales.append(pred_sales)
            forecast_records.append({
                'date': date_str,
                'store_nbr': store_nbr,
                'family': family,
                'forecast_horizon_day': step_idx + 1,
                'predicted_sales': round(pred_sales, 2),
                'dayofweek': cur_date.dayofweek,
                'onpromotion': promo_val,
                'is_holiday': is_hol,
                'oil_price': round(oil_price, 2)
            })

        return pd.DataFrame(forecast_records)


class GenericTimeSeriesForecaster:
    """Fallback recursive forecaster for arbitrary single-series time-series datasets."""
    def forecast(
        self,
        df: pd.DataFrame,
        date_col: str,
        target_col: str,
        horizon: int = 14
    ) -> pd.DataFrame:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).dropna(subset=[target_col])
        if len(df) < 14:
            raise DataValidationError(f"Time series requires at least 14 historical points, found {len(df)}.")

        # Fit lightweight XGBoost regressor on simple lags and calendar coordinates
        df['dayofweek'] = df[date_col].dt.dayofweek
        df['month'] = df[date_col].dt.month
        df['day'] = df[date_col].dt.day
        for l in [1, 2, 7]:
            df[f'lag_{l}'] = df[target_col].shift(l)
        df['rolling_mean_7'] = df[target_col].shift(1).rolling(7, min_periods=1).mean()

        train_data = df.dropna().copy()
        feats = ['dayofweek', 'month', 'day', 'lag_1', 'lag_2', 'lag_7', 'rolling_mean_7']
        X = train_data[feats]
        y = train_data[target_col]

        model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.08, random_state=42)
        model.fit(X, y)

        last_date = df[date_col].max()
        history = list(df[target_col].values)
        out_dates = pd.date_range(last_date + timedelta(days=1), periods=horizon, freq='D')
        
        preds = []
        for i, dt in enumerate(out_dates):
            lag_1 = history[-1]
            lag_2 = history[-2] if len(history) >= 2 else lag_1
            lag_7 = history[-7] if len(history) >= 7 else lag_1
            roll_7 = float(np.mean(history[-7:]))
            row = pd.DataFrame([{
                'dayofweek': dt.dayofweek,
                'month': dt.month,
                'day': dt.day,
                'lag_1': lag_1,
                'lag_2': lag_2,
                'lag_7': lag_7,
                'rolling_mean_7': roll_7
            }])[feats]
            p = float(np.clip(model.predict(row)[0], 0, None))
            history.append(p)
            preds.append({
                'date': dt.strftime('%Y-%m-%d'),
                'forecast_horizon_day': i + 1,
                'predicted_sales': round(p, 2),
                'dayofweek': dt.dayofweek,
                'onpromotion': 0.0,
                'is_holiday': 0,
                'oil_price': None
            })
        return pd.DataFrame(preds)
