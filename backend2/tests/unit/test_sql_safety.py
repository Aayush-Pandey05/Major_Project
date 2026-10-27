"""
test_sql_safety.py
==================
Tests read-only SQL security validation.
Verifies that all mutations and dangerous administrative statements are rejected.
"""
import pytest
from app.services.database_tools.sql_connector import ReadOnlySQLConnector
from app.core.exceptions import UnsafeSQLError

def test_safe_select_queries_pass():
    ReadOnlySQLConnector.validate_query("SELECT id, name FROM users WHERE active = 1")
    ReadOnlySQLConnector.validate_query("SELECT count(*) as total, region FROM sales GROUP BY region")
    ReadOnlySQLConnector.validate_query("WITH summary AS (SELECT * FROM orders) SELECT * FROM summary")

@pytest.mark.parametrize("query", [
    "INSERT INTO users (name) VALUES ('hacker')",
    "UPDATE users SET role = 'admin'",
    "DELETE FROM logs WHERE created_at < '2020-01-01'",
    "DROP TABLE critical_data",
    "ALTER TABLE users ADD COLUMN compromised INT",
    "TRUNCATE TABLE audit_log",
    "SELECT * FROM users; DROP TABLE orders;",
    "GRANT ALL PRIVILEGES ON DATABASE mydb TO evil",
    "EXEC sp_executesql N'SELECT 1'",
    "SELECT * INTO OUTFILE '/tmp/dump.txt' FROM users"
])
def test_unsafe_queries_are_strictly_rejected(query: str):
    with pytest.raises(UnsafeSQLError):
        ReadOnlySQLConnector.validate_query(query)
