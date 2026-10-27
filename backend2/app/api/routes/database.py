"""
database.py
===========
External read-only SQL database management and query routes.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.services.database_tools.sql_connector import ReadOnlySQLConnector
from app.core.exceptions import UnsafeSQLError

router = APIRouter(prefix="/database", tags=["External Database"])

class DBTestRequest(BaseModel):
    connection_url: str

class DBSchemaRequest(BaseModel):
    connection_url: str

class DBQueryRequest(BaseModel):
    connection_url: str
    query: str
    max_rows: Optional[int] = 100

@router.post("/test")
async def test_db_connection(req: DBTestRequest):
    return ReadOnlySQLConnector.test_connection(req.connection_url)

@router.post("/schema")
async def get_db_schema(req: DBSchemaRequest):
    try:
        return ReadOnlySQLConnector.get_schema_metadata(req.connection_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query")
async def execute_read_only_query(req: DBQueryRequest):
    try:
        res = ReadOnlySQLConnector.execute_read_only(
            connection_url=req.connection_url,
            sql_query=req.query,
            max_rows=req.max_rows
        )
        return res
    except UnsafeSQLError as e:
        raise HTTPException(status_code=403, detail=f"Query rejected by read-only security policy: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution error: {str(e)}")
