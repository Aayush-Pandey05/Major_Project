"""
loader.py
=========
Safe in-memory CSV/Excel dataset loader.
Computes and verifies SHA-256 checksums before and after reading to guarantee
the uploaded source file is strictly immutable and never modified.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Tuple, Union
import pandas as pd

from app.core.exceptions import DataValidationError, ReadOnlyViolationError
from app.core.logging import logger

class DatasetLoader:
    @staticmethod
    def compute_sha256(file_path: Union[str, Path]) -> str:
        p = Path(file_path)
        if not p.exists():
            raise DataValidationError(f"File not found: {p}")
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def load_dataset(
        cls,
        file_path: Union[str, Path]
    ) -> Tuple[pd.DataFrame, str]:
        """
        Loads dataset into in-memory DataFrame while strictly asserting source immutability.
        Returns (in-memory DataFrame, sha256_checksum).
        """
        p = Path(file_path)
        if not p.exists():
            raise DataValidationError(f"Source file not found: {p}")

        initial_checksum = cls.compute_sha256(p)
        suffix = p.suffix.lower()

        try:
            if suffix == ".csv":
                for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
                    try:
                        df = pd.read_csv(p, encoding=enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise DataValidationError(f"Unable to decode CSV file {p.name}")
            elif suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(p)
            elif suffix == ".parquet":
                df = pd.read_parquet(p)
            else:
                raise DataValidationError(f"Unsupported file format: {suffix}")
        except Exception as e:
            raise DataValidationError(f"Failed to read file {p.name}: {e}") from e

        # Assert checksum is still identical (strict immutability proof)
        post_checksum = cls.compute_sha256(p)
        if post_checksum != initial_checksum:
            raise ReadOnlyViolationError(f"CRITICAL: Source file {p.name} checksum modified during read operation!")

        logger.debug(f"Loaded {p.name} ({len(df)} rows, {len(df.columns)} cols). SHA-256: {initial_checksum[:12]}...")
        # Return a detached copy to ensure in-memory modifications don't reflect on disk
        return df.copy(), initial_checksum
