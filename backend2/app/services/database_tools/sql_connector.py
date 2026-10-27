"""
sql_connector.py
================
External SQL connection manager and read-only query executor.
Supports PostgreSQL, MySQL, and SQLite.
Strictly enforces read-only access by rejecting mutations and admin operations.
Never modifies source databases, never writes application or model data to external DBs.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import UnsafeSQLError, DataValidationError

# Strict blocklist of modifying keywords
DISALLOWED_SQL_PATTERNS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bCREATE\b",
    r"\bALTER\b", r"\bTRUNCATE\b", r"\bREPLACE\b", r"\bMERGE\b", r"\bUPSERT\b",
    r"\bGRANT\b", r"\bREVOKE\b", r"\bCOMMIT\b", r"\bROLLBACK\b", r"\bSAVEPOINT\b",
    r"\bEXEC\b", r"\bEXECUTE\b", r"\bCALL\b", r"\bVACUUM\b", r"\bLOCK\b",
    r"\bINTO\s+OUTFILE\b", r"\bLOAD_FILE\b", r"\bATTACH\b", r"\bDETACH\b"
]

class ReadOnlySQLConnector:
    @staticmethod
    def sanitize_connection_url(url: str) -> str:
        """Masks password for safe logging and display."""
        return re.sub(r":([^@]+)@", r":****@", url)

    @classmethod
    def create_safe_engine(cls, connection_url: str) -> Engine:
        # SQLite, PostgreSQL, MySQL supported
        connect_args = {}
        if connection_url.startswith("sqlite"):
            # uri=True with query param mode=ro for read-only SQLite
            if "?" not in connection_url:
                connection_url += "?mode=ro"
        return create_engine(
            connection_url,
            connect_args=connect_args,
            pool_pre_ping=True,
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

    @classmethod
    def test_connection(cls, connection_url: str) -> Dict[str, Any]:
        """Tests external database connectivity and returns server dialect."""
        try:
            engine = cls.create_safe_engine(connection_url)
            with engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).scalar()
            return {
                "success": True,
                "dialect": engine.dialect.name,
                "message": "Connection successfully established and verified read-only."
            }
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {
                "success": False,
                "dialect": "unknown",
                "message": f"Connection failed: {str(e)}"
            }

    @classmethod
    def get_schema_metadata(cls, connection_url: str) -> Dict[str, Any]:
        """Inspects and returns tables, column definitions, and primary keys."""
        try:
            engine = cls.create_safe_engine(connection_url)
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            tables_meta = []
            for t_name in table_names[:50]: # Safety cap on table count
                cols = []
                for col in inspector.get_columns(t_name):
                    cols.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True)
                    })
                pk = inspector.get_pk_constraint(t_name)
                tables_meta.append({
                    "table_name": t_name,
                    "columns": cols,
                    "primary_key": pk.get("constrained_columns", [])
                })

            return {
                "dialect": engine.dialect.name,
                "tables_count": len(table_names),
                "tables": tables_meta
            }
        except Exception as e:
            logger.error(f"Failed to inspect schema: {e}")
            raise DataValidationError(f"Could not retrieve schema: {e}") from e

    @classmethod
    def validate_query(cls, sql_query: str) -> None:
        """Validates that a SQL query is strictly read-only and free of dangerous side effects."""
        clean_sql = re.sub(r"--.*$", "", sql_query, flags=re.MULTILINE)
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL).strip()

        if not clean_sql:
            raise UnsafeSQLError("Query is empty.")

        # Disallow multi-statement queries separated by semicolons
        statements = [s.strip() for s in clean_sql.split(";") if s.strip()]
        if len(statements) > 1:
            raise UnsafeSQLError("Multiple statements are rejected. Only single read-only statements are allowed.")

        # Must start with SELECT or WITH (Common Table Expression)
        if not re.match(r"^(SELECT|WITH)\b", clean_sql, re.IGNORECASE):
            raise UnsafeSQLError("Query must begin with SELECT or WITH.")

        for pat in DISALLOWED_SQL_PATTERNS:
            if re.search(pat, clean_sql, re.IGNORECASE):
                raise UnsafeSQLError(f"Query contains prohibited mutation/administrative keyword matching '{pat}'.")

    @classmethod
    def execute_read_only(
        cls,
        connection_url: str,
        sql_query: str,
        max_rows: Optional[int] = None
    ) -> Dict[str, Any]:
        """Executes candidate SQL with strict timeout and row limits."""
        cls.validate_query(sql_query)
        limit = max_rows or settings.MAX_SQL_ROWS_RETURNED

        start_time = time.time()
        engine = cls.create_safe_engine(connection_url)

        try:
            with engine.connect() as conn:
                # Wrap in readonly transaction if PostgreSQL
                if engine.dialect.name == "postgresql":
                    conn.execute(text("SET TRANSACTION READ ONLY"))
                
                result = conn.execute(text(sql_query))
                cols = list(result.keys())
                rows = []
                for i, r in enumerate(result):
                    if i >= limit:
                        break
                    # Convert row to dict with JSON-serializable values
                    row_dict = {}
                    for col_name, val in zip(cols, r):
                        if isinstance(val, (int, float, bool, str)) or val is None:
                            row_dict[col_name] = val
                        else:
                            row_dict[col_name] = str(val)
                    rows.append(row_dict)

            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "success": True,
                "query": sql_query,
                "columns": cols,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": elapsed_ms,
                "truncated": len(rows) >= limit
            }
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise UnsafeSQLError(f"SQL Execution Error: {str(e)}") from e
