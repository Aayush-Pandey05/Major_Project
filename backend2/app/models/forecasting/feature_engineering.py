"""
feature_engineering.py
----------------------
Reusable, leak-free feature engineering pipeline for Store Sales Time-Series Forecasting.
Provides functions for:
- Calendar & seasonal features
- Historical lag features (grouped by store and product family)
- Historical rolling statistics using shifted windows (preventing future target leakage)
- External covariates: Oil price imputation, lags, and rolling trends
- Holiday & calendar events integration
- Step-by-step recursive lag extraction for multi-step horizon forecasting
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

def add_calendar_features(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    df = df.copy()
    if not np.issubdtype(df[date_col].dtype, np.datetime64):
        df[date_col] = pd.to_datetime(df[date_col])
        
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day'] = df[date_col].dt.day
    df['dayofweek'] = df[date_col].dt.dayofweek
    df['dayofyear'] = df[date_col].dt.dayofyear
    df['weekofyear'] = df[date_col].dt.isocalendar().week.astype(int)
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    return df

def preprocess_oil_data(oil_df: pd.DataFrame, full_date_range: pd.DatetimeIndex) -> pd.DataFrame:
    oil = oil_df.copy()
    if not np.issubdtype(oil['date'].dtype, np.datetime64):
        oil['date'] = pd.to_datetime(oil['date'])
        
    calendar_df = pd.DataFrame({'date': full_date_range})
    oil_merged = pd.merge(calendar_df, oil, on='date', how='left')
    oil_merged['dcoilwtico'] = oil_merged['dcoilwtico'].bfill().ffill()
    oil_merged['oil_lag_1'] = oil_merged['dcoilwtico'].shift(1).bfill()
    oil_merged['oil_rolling_mean_7'] = (
        oil_merged['dcoilwtico'].shift(1).rolling(7, min_periods=1).mean().bfill()
    )
    return oil_merged[['date', 'dcoilwtico', 'oil_lag_1', 'oil_rolling_mean_7']]

def preprocess_holiday_data(holidays_df: pd.DataFrame, full_date_range: pd.DatetimeIndex) -> pd.DataFrame:
    holidays = holidays_df.copy()
    if not np.issubdtype(holidays['date'].dtype, np.datetime64):
        holidays['date'] = pd.to_datetime(holidays['date'])
        
    valid_holidays = holidays[~holidays['transferred'] & (holidays['type'] != 'Work Day')].copy()
    holiday_daily = valid_holidays.groupby('date').agg(
        is_holiday=('type', lambda x: 1),
        is_national_holiday=('locale', lambda x: int((x == 'National').any()))
    ).reset_index()
    
    work_days = holidays[holidays['type'] == 'Work Day'][['date']].drop_duplicates()
    work_days['is_workday'] = 1
    
    calendar_df = pd.DataFrame({'date': full_date_range})
    holiday_features = pd.merge(calendar_df, holiday_daily, on='date', how='left')
    holiday_features = pd.merge(holiday_features, work_days, on='date', how='left')
    holiday_features['is_holiday'] = holiday_features['is_holiday'].fillna(0).astype(int)
    holiday_features['is_national_holiday'] = holiday_features['is_national_holiday'].fillna(0).astype(int)
    holiday_features['is_workday'] = holiday_features['is_workday'].fillna(0).astype(int)
    return holiday_features[['date', 'is_holiday', 'is_national_holiday', 'is_workday']]

def compute_step_lags_and_rolling(
    history_sales: List[float],
    lags: List[int] = [1, 7, 14, 28],
    rolling_windows: List[int] = [7, 14, 28]
) -> Dict[str, float]:
    n = len(history_sales)
    feat_dict = {}
    for lag in lags:
        if n >= lag:
            feat_dict[f'sales_lag_{lag}'] = float(history_sales[-lag])
        else:
            feat_dict[f'sales_lag_{lag}'] = float(history_sales[0]) if n > 0 else 0.0
            
    for w in rolling_windows:
        w_slice = history_sales[-w:] if n >= w else history_sales
        feat_dict[f'sales_rolling_mean_{w}'] = float(np.mean(w_slice)) if len(w_slice) > 0 else 0.0
        
    for w in [7, 28]:
        w_slice = history_sales[-w:] if n >= w else history_sales
        feat_dict[f'sales_rolling_std_{w}'] = float(np.std(w_slice)) if len(w_slice) > 1 else 0.0
        
    return feat_dict

FEATURE_COLUMNS = [
    'store_nbr', 'family', 'type', 'cluster', 'city', 'state',
    'onpromotion', 'dcoilwtico', 'oil_lag_1', 'oil_rolling_mean_7',
    'is_holiday', 'is_national_holiday', 'is_workday',
    'year', 'month', 'day', 'dayofweek', 'dayofyear', 'weekofyear', 'is_weekend',
    'sales_lag_1', 'sales_lag_7', 'sales_lag_14', 'sales_lag_28',
    'sales_rolling_mean_7', 'sales_rolling_mean_14', 'sales_rolling_mean_28',
    'sales_rolling_std_7', 'sales_rolling_std_28'
]
