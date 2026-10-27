"""
datasets.py
===========
Dataset inspection, validation, and profiling routes for Backend 2.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Any, Dict, Optional
from pathlib import Path
import shutil
import uuid

from app.core.config import settings
from app.services.data_profiling.profiler import DatasetProfiler

router = APIRouter(prefix="/datasets", tags=["Datasets"])

class ProfileRequest(BaseModel):
    file_path: Optional[str] = None

@router.post("/profile")
async def profile_dataset(req: ProfileRequest):
    if not req.file_path:
        raise HTTPException(status_code=400, detail="file_path is required")
    p = Path(req.file_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {p}")
    try:
        profile = DatasetProfiler.profile(p)
        return profile
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Profiling failed: {str(e)}")

@router.post("/upload")
async def upload_dataset_direct(file: UploadFile = File(...)):
    """Receives file upload directly into Backend 2 storage with unique safe name."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".csv", ".xlsx", ".xls", ".parquet"]:
        raise HTTPException(status_code=400, detail="Only CSV, Excel, and Parquet files are supported.")

    unique_name = f"upload_{uuid.uuid4().hex[:8]}_{file.filename}"
    target_path = settings.UPLOADS_DIR / unique_name

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    profile = DatasetProfiler.profile(target_path)
    return {
        "file_name": unique_name,
        "original_name": file.filename,
        "file_path": str(target_path),
        "profile": profile
    }
