"""
results.py
==========
Result file download route for Backend 2.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import settings

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("/download/{filename}")
async def download_result_file(filename: str):
    # Prevent directory traversal
    clean_filename = Path(filename).name
    file_path = settings.RESULTS_DIR / clean_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found.")

    return FileResponse(
        path=file_path,
        filename=clean_filename,
        media_type="application/octet-stream"
    )
