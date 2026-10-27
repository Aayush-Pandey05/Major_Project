"""
config.py
=========
Central configuration for FastAPI Backend 2 using Pydantic Settings.
Reads configuration from environment variables and root .env safely.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine base paths
BACKEND2_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = BACKEND2_ROOT.parent

# Load environment variables into os.environ for LangChain/LangSmith/OpenAI
load_dotenv(WORKSPACE_ROOT / ".env")
load_dotenv(BACKEND2_ROOT / ".env", override=True)

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "Multi-Agent AI Data Analyst - Python Backend 2"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Network & Internal Auth
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND1_URL: str = "http://localhost:3001"
    INTERNAL_SERVICE_TOKEN: str = "dev-internal-secret-token"
    
    # OpenAI Integration (Only Orchestrator, SQL Agent, and Synthesis Agent use this)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # LangSmith Observability & Tracing
    LANGCHAIN_TRACING_V2: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "multi-agent-data-analyst"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    
    # Storage Paths
    UPLOADS_DIR: Path = BACKEND2_ROOT / "storage" / "uploads"
    RESULTS_DIR: Path = BACKEND2_ROOT / "storage" / "generated_results"
    MODEL_ARTIFACTS_DIR: Path = BACKEND2_ROOT / "app" / "models" / "artifacts"
    FORECAST_REF_DIR: Path = BACKEND2_ROOT / "app" / "models" / "forecasting" / "reference_data"
    
    # Security & Limits
    MAX_UPLOAD_SIZE_MB: int = 50
    SQL_QUERY_TIMEOUT_SECONDS: int = 15
    MAX_SQL_ROWS_RETURNED: int = 1000

    model_config = SettingsConfigDict(
        env_file=(WORKSPACE_ROOT / ".env", BACKEND2_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def init_directories(self) -> None:
        """Ensure runtime storage directories exist."""
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.MODEL_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        self.FORECAST_REF_DIR.mkdir(parents=True, exist_ok=True)

    def init_langsmith(self) -> None:
        """Propagate LangSmith configuration to os.environ for LangChain/LangGraph."""
        import os
        if self.LANGCHAIN_API_KEY and self.LANGCHAIN_API_KEY.strip() and not self.LANGCHAIN_API_KEY.startswith("lsv2_pt_your"):
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.LANGCHAIN_API_KEY.strip()
            if self.LANGCHAIN_PROJECT:
                os.environ["LANGCHAIN_PROJECT"] = self.LANGCHAIN_PROJECT
            if self.LANGCHAIN_ENDPOINT:
                os.environ["LANGCHAIN_ENDPOINT"] = self.LANGCHAIN_ENDPOINT
        else:
            # Prevent 401 warnings if user has not yet entered their key
            os.environ["LANGCHAIN_TRACING_V2"] = "false"

settings = Settings()
settings.init_directories()
settings.init_langsmith()
