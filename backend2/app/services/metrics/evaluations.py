"""
evaluations.py
==============
Service for loading and exposing genuine model evaluation metrics and benchmarks.
Strictly surfaces real saved experimental results without fabricating metrics.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from app.core.config import settings

class ModelEvaluationService:
    @classmethod
    def get_anomaly_model_metrics(cls) -> Dict[str, Any]:
        meta_path = settings.MODEL_ARTIFACTS_DIR / "isolation_forest_metadata.json"
        if not meta_path.exists():
            return {"error": "Anomaly metadata not found."}

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "model_name": data.get("model_name"),
            "model_version": data.get("model_version"),
            "intended_use": data.get("intended_use"),
            "algorithm": data.get("model", {}).get("algorithm"),
            "hyperparameters": data.get("model", {}).get("params"),
            "contamination": data.get("model", {}).get("contamination"),
            "threshold_score": data.get("model", {}).get("threshold_anomaly_score"),
            "feature_names": data.get("feature_names"),
            "evaluation_summary": data.get("evaluation_summary"),
            "runtime": data.get("runtime"),
            "library_versions": data.get("library_versions")
        }

    @classmethod
    def get_forecasting_model_metrics(cls) -> Dict[str, Any]:
        meta_path = settings.MODEL_ARTIFACTS_DIR / "xgboost_metadata.json"
        if not meta_path.exists():
            return {"error": "Forecasting metadata not found."}

        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "model_name": data.get("model_name"),
            "model_version": data.get("model_version"),
            "target_variable": data.get("target_variable"),
            "primary_metric": data.get("primary_metric"),
            "train_date_range": data.get("train_date_range"),
            "validation_date_range": data.get("validation_date_range"),
            "hyperparameters": data.get("hyperparameters"),
            "evaluation_metrics": data.get("evaluation_metrics"),
            "feature_columns": data.get("feature_columns"),
            "categorical_features": data.get("categorical_features"),
            "forecast_strategy": data.get("forecast_strategy")
        }

    @classmethod
    def get_all_evaluations(cls) -> Dict[str, Any]:
        return {
            "anomaly_detection": cls.get_anomaly_model_metrics(),
            "forecasting": cls.get_forecasting_model_metrics()
        }
