"""
exceptions.py
=============
Custom exception hierarchy for Backend 2.
"""
from typing import Any, Dict, Optional

class BackendException(Exception):
    """Base exception for Backend 2 domain errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataValidationError(BackendException):
    """Raised when an uploaded file or input dataset cannot be processed."""
    pass

class ReadOnlyViolationError(BackendException):
    """Raised when an attempt is made to mutate source files or connected external databases."""
    pass

class ModelInferenceError(BackendException):
    """Raised when an anomaly detection or forecasting model fails during inference."""
    pass

class UnsafeSQLError(BackendException):
    """Raised when a candidate SQL query fails read-only security checks."""
    pass

class AgentWorkflowError(BackendException):
    """Raised when orchestrator or agent execution encounters an unrecoverable state."""
    pass
