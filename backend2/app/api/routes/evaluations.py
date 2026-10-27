"""
evaluations.py
==============
Model evaluation metrics routes for Backend 2.
"""
from fastapi import APIRouter
from app.services.metrics.evaluations import ModelEvaluationService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

@router.get("")
async def get_evaluations():
    return ModelEvaluationService.get_all_evaluations()

@router.get("/anomaly")
async def get_anomaly_evaluations():
    return ModelEvaluationService.get_anomaly_model_metrics()

@router.get("/forecasting")
async def get_forecasting_evaluations():
    return ModelEvaluationService.get_forecasting_model_metrics()
