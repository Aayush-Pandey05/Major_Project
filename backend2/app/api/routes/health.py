"""
health.py
=========
Health check route for FastAPI Backend 2.
"""
from fastapi import APIRouter
from app.core.config import settings
from app.services.metrics.evaluations import ModelEvaluationService

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "models": {
            "isolation_forest": (settings.MODEL_ARTIFACTS_DIR / "isolation_forest_retail_model.joblib").exists(),
            "xgboost_sales": (settings.MODEL_ARTIFACTS_DIR / "xgboost_sales_forecasting_model.joblib").exists(),
        },
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }
