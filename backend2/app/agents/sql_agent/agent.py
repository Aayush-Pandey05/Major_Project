"""
agent.py
========
SQL Agent: Translates natural language queries into safe, read-only SQL queries
and executes them against connected databases. Enforces strict read-only policy.
Never executes data mutations (INSERT, UPDATE, DELETE, DROP, ALTER) or administrative statements.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import UnsafeSQLError, DataValidationError
from app.services.database_tools.sql_connector import ReadOnlySQLConnector

class SQLAgentResult(BaseModel):
    generated_sql: str
    execution_result: Optional[Dict[str, Any]] = None
    row_count: int = 0
    columns: List[str] = []
    error: Optional[str] = None
    explanation: Optional[str] = None

class SQLAgent:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL

    def execute_query(
        self,
        query: str,
        connection_url: str,
        schema_metadata: Optional[Dict[str, Any]] = None
    ) -> SQLAgentResult:
        """Translates user natural language into safe SQL and executes it."""
        # 1. Generate candidate SQL
        try:
            candidate_sql = self._generate_sql(query, connection_url, schema_metadata)
        except Exception as e:
            return SQLAgentResult(
                generated_sql="",
                error=f"SQL Generation Error: {str(e)}"
            )

        # 2. Validate against read-only policy
        try:
            ReadOnlySQLConnector.validate_query(candidate_sql)
        except UnsafeSQLError as e:
            logger.warning(f"Unsafe SQL blocked: {candidate_sql}. Reason: {e}")
            return SQLAgentResult(
                generated_sql=candidate_sql,
                error=f"Security Policy Rejection: {str(e)}"
            )

        # 3. Execute query
        try:
            exec_res = ReadOnlySQLConnector.execute_read_only(connection_url, candidate_sql)
            return SQLAgentResult(
                generated_sql=candidate_sql,
                execution_result=exec_res,
                row_count=exec_res["row_count"],
                columns=exec_res["columns"],
                explanation=f"Executed read-only SQL successfully in {exec_res['execution_time_ms']} ms."
            )
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return SQLAgentResult(
                generated_sql=candidate_sql,
                error=f"Execution Failed: {str(e)}"
            )

    def _generate_sql(
        self,
        query: str,
        connection_url: str,
        schema_metadata: Optional[Dict[str, Any]]
    ) -> str:
        # Check if query is already a raw SELECT statement
        clean_q = query.strip().rstrip(";")
        if re.match(r"^(SELECT|WITH)\b", clean_q, re.IGNORECASE):
            return clean_q

        if not schema_metadata:
            schema_metadata = ReadOnlySQLConnector.get_schema_metadata(connection_url)

        # Use OpenAI if available
        if self.api_key:
            return self._generate_sql_with_llm(query, schema_metadata)

        # Deterministic simple fallback for natural language
        tables = schema_metadata.get("tables", [])
        if tables:
            first_table = tables[0]["table_name"]
            first_cols = [c["name"] for c in tables[0]["columns"][:5]]
            cols_str = ", ".join(first_cols) if first_cols else "*"
            return f"SELECT {cols_str} FROM {first_table} LIMIT 50"

        raise DataValidationError("No tables accessible to query in the connected database.")

    def _generate_sql_with_llm(
        self,
        query: str,
        schema_metadata: Dict[str, Any]
    ) -> str:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.0
        )

        schema_summary = []
        for t in schema_metadata.get("tables", [])[:20]:
            col_list = [f"{c['name']} ({c['type']})" for c in t.get("columns", [])]
            schema_summary.append(f"Table '{t['table_name']}': {', '.join(col_list)}")

        system_prompt = (
            "You are a strict Read-Only SQL Agent.\n"
            "Generate ONLY a single read-only SELECT or WITH SQL query for the user query.\n"
            "Rules:\n"
            "- ONLY generate SELECT or WITH queries.\n"
            "- NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or CREATE.\n"
            "- Return ONLY the raw SQL code without markdown quotes, backticks or commentary.\n"
            "- Limit results to 100 rows if no limit is specified."
        )

        user_content = (
            f"Database Schema:\n" + "\n".join(schema_summary) + f"\n\nUser Question: {query}"
        )

        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
        sql_text = response.content.strip()
        sql_text = re.sub(r"^```sql\s*", "", sql_text, flags=re.IGNORECASE)
        sql_text = re.sub(r"^```\s*", "", sql_text)
        sql_text = re.sub(r"\s*```$", "", sql_text).strip()
        return sql_text
