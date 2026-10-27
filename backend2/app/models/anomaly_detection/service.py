"""
service.py
==========
High-level service orchestrating anomaly detection.
Preserves strict source immutability by operating entirely on in-memory copies
and saving outputs to separate results directory.
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
from app.models.anomaly_detection.inference import RetailAnomalyDetector, GenericTabularAnomalyDetector
from app.models.anomaly_detection.schemas import AnomalyDetectionResponse
from app.models.anomaly_detection.feature_engineering import standardize_columns

class AnomalyDetectionService:
    def __init__(self):
        self._retail_detector: Optional[RetailAnomalyDetector] = None

    def _get_retail_detector(self) -> RetailAnomalyDetector:
        if self._retail_detector is None:
            self._retail_detector = RetailAnomalyDetector()
        return self._retail_detector

    def is_retail_schema(self, df: pd.DataFrame) -> bool:
        """Determines if the dataset has columns matching the retail schema."""
        try:
            standardize_columns(df)
            return True
        except Exception:
            return False

    def detect_anomalies(
        self,
        data: Union[str, Path, pd.DataFrame],
        explain: str = "flagged",
        top_n: int = 50,
        contamination: Optional[float] = None
    ) -> AnomalyDetectionResponse:
        """
        Executes anomaly detection. Chooses retail pre-trained model for compatible
        datasets or generic unsupervised tabular detector for general datasets.
        Saves separate export CSV.
        """
        if isinstance(data, (str, Path)):
            p = Path(data)
            if not p.exists():
                raise DataValidationError(f"File not found: {p}")
            if p.suffix.lower() == ".csv":
                df = pd.read_csv(p)
            elif p.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(p)
            else:
                raise DataValidationError(f"Unsupported file format: {p.suffix}")
        elif isinstance(data, pd.DataFrame):
            df = data.copy() # In-memory defensive copy
        else:
            raise DataValidationError(f"Invalid data input: {type(data)}")

        if df.empty:
            raise DataValidationError("Input dataset is empty.")

        # Route to appropriate detector
        if self.is_retail_schema(df):
            logger.info("Dataset matches retail schema. Running pre-trained Isolation Forest model.")
            detector = self._get_retail_detector()
            res = detector.predict(df, explain=explain, top_n=top_n)
        else:
            logger.info("Dataset has arbitrary schema. Running generic tabular Isolation Forest detector.")
            cont = contamination if contamination and 0.0 < contamination < 0.5 else 0.02
            generic_detector = GenericTabularAnomalyDetector(contamination=cont)
            res = generic_detector.fit_predict(df, top_n=top_n)

        # Export result to separate storage (source file is NEVER modified)
        export_filename = f"anomaly_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.csv"
        export_path = settings.RESULTS_DIR / export_filename
        
        full_df = res.pop("full_scored_dataframe")
        full_df.to_csv(export_path, index=False)
        logger.info(f"Anomaly results saved separately to {export_path}")

        return AnomalyDetectionResponse(
            model_name=res["model_name"],
            model_version=res["model_version"],
            total_records_analyzed=res["total_records_analyzed"],
            anomalies_flagged_count=res["anomalies_flagged_count"],
            anomaly_percentage=res["anomaly_percentage"],
            threshold_score=res["threshold_score"],
            flagged_records=res["flagged_records"],
            findings=res["findings"],
            score_distribution=res["score_distribution"],
            export_file_url=f"/api/v1/results/download/{export_filename}",
            warning=res.get("warning")
        )
