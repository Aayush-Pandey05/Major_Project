"""
schemas.py
==========
Pydantic schemas for anomaly detection inputs, results, and diagnostics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class UnusualFeature(BaseModel):
    feature: str
    value: float
    score_contribution: float
    training_median: Optional[float] = None
    percentile_of_training: Optional[float] = None
    direction: Optional[str] = None
    above_training_max: Optional[bool] = None

class AnomalyFinding(BaseModel):
    invoice: str
    is_anomaly: bool
    prediction: int
    anomaly_score: float
    decision_function: float
    anomaly_rank: int
    score_percentile_vs_training: Optional[float] = None
    invoice_datetime: Optional[str] = None
    customer_id: Optional[str] = None
    country: Optional[str] = None
    features: Dict[str, float] = Field(default_factory=dict)
    unusual_features: List[UnusualFeature] = Field(default_factory=list)
    all_feature_contributions: Dict[str, float] = Field(default_factory=dict)
    explanation: Optional[str] = None

class AnomalyDetectionRequest(BaseModel):
    dataset_path: Optional[str] = None
    explain: str = "flagged" # 'flagged' | 'all' | 'none'
    top_n: int = 50
    contamination: Optional[float] = None

class AnomalyDetectionResponse(BaseModel):
    model_name: str = "isolation_forest_retail_model"
    model_version: str = "1.0.0"
    total_records_analyzed: int
    anomalies_flagged_count: int
    anomaly_percentage: float
    threshold_score: float
    flagged_records: List[Dict[str, Any]]
    findings: List[AnomalyFinding]
    score_distribution: Dict[str, float]
    export_file_url: Optional[str] = None
    warning: Optional[str] = None
