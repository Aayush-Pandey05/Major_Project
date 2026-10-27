"""
test_models.py
==============
Tests for migrated Isolation Forest and XGBoost model artifacts in Backend 2.
"""
import pytest
import pandas as pd
from app.models.anomaly_detection.service import AnomalyDetectionService
from app.models.forecasting.service import ForecastingService

def test_isolation_forest_loads_and_infers():
    service = AnomalyDetectionService()
    sample_df = pd.DataFrame([
        {'Invoice': '536365', 'StockCode': '85123A', 'Quantity': 6, 'InvoiceDate': '2010-12-01 08:26:00', 'Price': 2.55},
        {'Invoice': '536365', 'StockCode': '71053', 'Quantity': 6, 'InvoiceDate': '2010-12-01 08:26:00', 'Price': 3.39},
        {'Invoice': '536366', 'StockCode': '22633', 'Quantity': 10000, 'InvoiceDate': '2010-12-01 08:28:00', 'Price': 999.00}
    ])
    
    res = service.detect_anomalies(sample_df, top_n=5)
    assert res.total_records_analyzed == 2
    assert res.anomalies_flagged_count >= 1
    assert res.threshold_score > 0
    assert len(res.findings) >= 1
    assert res.findings[0].invoice in ['536365', '536366']

def test_xgboost_forecaster_loads_and_infers():
    service = ForecastingService()
    res = service.forecast_sales(store_nbr=1, family="GROCERY I", start_date="2017-08-16", horizon=7)
    
    assert res.horizon_days == 7
    assert len(res.forecasts) == 7
    assert res.forecasts[0].predicted_sales > 0
    assert res.store_nbr == 1
    assert res.family == "GROCERY I"
    assert "total_forecast_sales" in res.historical_summary
