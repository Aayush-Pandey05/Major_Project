"""
test_immutability.py
====================
Verifies that uploaded source files are NEVER modified, appended to, or overwritten.
Ensures SHA-256 checksum remains 100% identical before and after all analytical workflows.
"""
import hashlib
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from app.services.csv_excel.loader import DatasetLoader
from app.services.data_profiling.profiler import DatasetProfiler
from app.models.anomaly_detection.service import AnomalyDetectionService

def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(4096):
            h.update(chunk)
    return h.hexdigest()

def test_source_file_remains_strictly_unchanged():
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n")
        f.write("536365,85123A,WHITE HANGING HEART T-LIGHT HOLDER,6,12/1/2010 8:26,2.55,17850,United Kingdom\n")
        f.write("536366,22633,HAND WARMER UNION JACK,10000,12/1/2010 8:28,999.00,17850,United Kingdom\n")
        temp_csv = Path(f.name)

    try:
        initial_checksum = _compute_sha256(temp_csv)
        initial_size = temp_csv.stat().st_size
        initial_content = temp_csv.read_bytes()

        # 1. Profile the dataset
        profile = DatasetProfiler.profile(temp_csv)
        assert profile["row_count"] == 2

        # 2. Run full Anomaly Detection analysis
        service = AnomalyDetectionService()
        result = service.detect_anomalies(data=temp_csv, top_n=10)
        assert result.anomalies_flagged_count >= 1

        # 3. Assert file checksum and contents are completely unchanged
        final_checksum = _compute_sha256(temp_csv)
        final_size = temp_csv.stat().st_size
        final_content = temp_csv.read_bytes()

        assert initial_checksum == final_checksum, "Source file SHA-256 changed!"
        assert initial_size == final_size, "Source file byte size changed!"
        assert initial_content == final_content, "Source file content was altered!"
        
        # 4. Assert separate export exists and is NOT the original file
        export_file = Path(result.export_file_url.split("/download/")[1])
        assert export_file.name != temp_csv.name
    finally:
        if temp_csv.exists():
            temp_csv.unlink()
