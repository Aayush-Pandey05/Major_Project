"""
profiler.py
===========
Profiles uploaded datasets (CSV, Excel) to provide comprehensive metadata,
statistical summaries, date and target column detection, and data previews.
Operates strictly in-memory without modifying the source file.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from app.core.exceptions import DataValidationError
from app.services.csv_excel.loader import DatasetLoader

CANDIDATE_TARGET_NAMES = {
    "sales", "revenue", "profit", "amount", "total", "price", "unitprice",
    "quantity", "qty", "target", "value", "cost", "demand"
}

class DatasetProfiler:
    @classmethod
    def profile(
        cls,
        data: Union[str, Path, pd.DataFrame]
    ) -> Dict[str, Any]:
        if isinstance(data, (str, Path)):
            df, checksum = DatasetLoader.load_dataset(data)
            file_name = Path(data).name
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
            checksum = "in_memory"
            file_name = "in_memory_dataset"
        else:
            raise DataValidationError(f"Invalid input data type: {type(data)}")

        row_count, col_count = df.shape
        duplicate_count = int(df.duplicated().sum())

        col_details = []
        date_candidates = []
        target_candidates = []
        numerical_summary = {}

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            missing_pct = round((missing_count / row_count * 100.0) if row_count > 0 else 0.0, 2)
            unique_count = int(series.nunique(dropna=True))

            # Detect data type and possible date column
            is_numeric = pd.api.types.is_numeric_dtype(series)
            is_datetime = pd.api.types.is_datetime64_any_dtype(series)
            
            clean_name = re.sub(r"[^a-z]", "", str(col).lower())
            if not is_datetime and series.dropna().shape[0] > 0 and clean_name in ["date", "invoicedate", "time", "timestamp", "datetime", "day"]:
                # Try parsing as datetime
                try:
                    sample = series.dropna().head(20)
                    pd.to_datetime(sample)
                    date_candidates.append(str(col))
                except Exception:
                    pass
            elif is_datetime:
                date_candidates.append(str(col))

            if is_numeric and clean_name in CANDIDATE_TARGET_NAMES:
                target_candidates.append(str(col))

            samples = [str(v) if pd.notna(v) else None for v in series.dropna().head(3).tolist()]

            col_details.append({
                "column_name": str(col),
                "data_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_percentage": missing_pct,
                "unique_count": unique_count,
                "is_numeric": is_numeric,
                "sample_values": samples
            })

            if is_numeric and unique_count > 0:
                s_num = pd.to_numeric(series, errors="coerce").dropna()
                if len(s_num) > 0:
                    numerical_summary[str(col)] = {
                        "mean": round(float(s_num.mean()), 2),
                        "std": round(float(s_num.std()), 2) if len(s_num) > 1 else 0.0,
                        "min": round(float(s_num.min()), 2),
                        "p25": round(float(s_num.quantile(0.25)), 2),
                        "median": round(float(s_num.median()), 2),
                        "p75": round(float(s_num.quantile(0.75)), 2),
                        "max": round(float(s_num.max()), 2)
                    }

        preview_records = []
        for _, row in df.head(10).iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    record[str(col)] = None
                elif isinstance(val, (int, float, bool, str)):
                    record[str(col)] = val
                else:
                    record[str(col)] = str(val)
            preview_records.append(record)

        return {
            "file_name": file_name,
            "sha256": checksum,
            "row_count": row_count,
            "column_count": col_count,
            "duplicate_row_count": duplicate_count,
            "columns": col_details,
            "identified_date_columns": date_candidates,
            "candidate_target_columns": target_candidates if target_candidates else [c for c in numerical_summary.keys()][:3],
            "numerical_summary": numerical_summary,
            "preview_rows": preview_records
        }
