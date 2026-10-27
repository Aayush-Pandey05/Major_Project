"""
exporter.py
===========
Saves separate analytical results, CSV exports, plots, and markdown reports.
Strictly ensures all generated outputs are stored separately from uploaded files.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.config import settings

class ResultExporter:
    @staticmethod
    def get_export_dir() -> Path:
        export_dir = settings.RESULTS_DIR
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    @classmethod
    def export_dataframe_csv(
        cls,
        df: pd.DataFrame,
        prefix: str = "result",
        description: str = "Generated analytical result"
    ) -> Dict[str, str]:
        """Saves DataFrame as a separate CSV file in results directory."""
        export_dir = cls.get_export_dir()
        file_id = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.csv"
        target_path = export_dir / file_id

        df.to_csv(target_path, index=False)
        return {
            "file_name": file_id,
            "file_path": str(target_path),
            "download_url": f"/api/v1/results/download/{file_id}",
            "description": description
        }

    @classmethod
    def export_markdown_report(
        cls,
        content: str,
        title: str = "Analytical Report",
        prefix: str = "report"
    ) -> Dict[str, str]:
        """Saves analytical narrative as a separate Markdown file in results directory."""
        export_dir = cls.get_export_dir()
        file_id = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.md"
        target_path = export_dir / file_id

        header = f"# {title}\n*Generated at {datetime.utcnow().isoformat()} UTC*\n\n---\n\n"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(header + content)

        return {
            "file_name": file_id,
            "file_path": str(target_path),
            "download_url": f"/api/v1/results/download/{file_id}"
        }
