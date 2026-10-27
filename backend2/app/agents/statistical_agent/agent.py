"""
agent.py
========
Statistical Agent: Performs deterministic statistical computations, descriptive summaries,
correlation matrices, and Isolation Forest anomaly detection.
STRICTLY NEVER CALLS OPENAI. All calculations, inference, and explanations are derived
deterministically from data and trained model mathematics.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.core.exceptions import DataValidationError
from app.models.anomaly_detection.service import AnomalyDetectionService
from app.models.anomaly_detection.schemas import AnomalyDetectionResponse
from app.services.csv_excel.loader import DatasetLoader

class StatisticalAgentResult(BaseModel):
    task_type: str # 'anomaly_detection' | 'correlation' | 'descriptive_summary'
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    anomaly_response: Optional[AnomalyDetectionResponse] = None
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    data_table: Optional[List[Dict[str, Any]]] = None
    description: str

class StatisticalAgent:
    def __init__(self):
        self.anomaly_service = AnomalyDetectionService()

    def run_analysis(
        self,
        data: Union[str, Path, pd.DataFrame],
        task: str = "anomaly_detection",
        params: Optional[Dict[str, Any]] = None
    ) -> StatisticalAgentResult:
        """Executes purely deterministic statistical analysis without LLM calls."""
        params = params or {}

        if isinstance(data, (str, Path)):
            df, _ = DatasetLoader.load_dataset(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise DataValidationError(f"Invalid data input: {type(data)}")

        if task == "anomaly_detection":
            top_n = params.get("top_n", 30)
            explain = params.get("explain", "flagged")
            contamination = params.get("contamination", None)
            
            anom_res = self.anomaly_service.detect_anomalies(
                data=df,
                explain=explain,
                top_n=top_n,
                contamination=contamination
            )

            metrics = {
                "total_records": anom_res.total_records_analyzed,
                "anomalies_flagged": anom_res.anomalies_flagged_count,
                "anomaly_percentage": anom_res.anomaly_percentage,
                "model_threshold": anom_res.threshold_score,
                "score_median": anom_res.score_distribution.get("median", 0.0),
                "score_p95": anom_res.score_distribution.get("p95", 0.0),
            }

            return StatisticalAgentResult(
                task_type="anomaly_detection",
                summary_metrics=metrics,
                anomaly_response=anom_res,
                data_table=anom_res.flagged_records,
                description=(
                    f"Isolation Forest identified {anom_res.anomalies_flagged_count} potential anomalies "
                    f"({anom_res.anomaly_percentage}% of {anom_res.total_records_analyzed} records analyzed)."
                )
            )

        elif task == "correlation":
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(num_cols) < 2:
                raise DataValidationError("At least 2 numeric columns are required to compute correlations.")

            corr_df = df[num_cols].corr(method="pearson").round(3)
            corr_dict = corr_df.to_dict()

            return StatisticalAgentResult(
                task_type="correlation",
                summary_metrics={"numeric_columns_count": len(num_cols)},
                correlation_matrix=corr_dict,
                data_table=corr_df.reset_index().rename(columns={"index": "column"}).to_dict(orient="records"),
                description=f"Computed Pearson correlation matrix across {len(num_cols)} numerical variables."
            )

        else: # descriptive summary
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            desc = df[num_cols].describe().round(2).reset_index()
            return StatisticalAgentResult(
                task_type="descriptive_summary",
                summary_metrics={"total_rows": len(df), "numeric_columns": len(num_cols)},
                data_table=desc.to_dict(orient="records"),
                description=f"Generated descriptive statistical summary across {len(num_cols)} numerical features."
            )
