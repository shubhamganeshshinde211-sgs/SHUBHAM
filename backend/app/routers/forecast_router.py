"""
Forecast Router: Endpoints for 3-Day & 7-Day Market Price Predictions and Walk-Forward Model Evaluations.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from backend.app.forecasting.schemas import MandiPriceForecast
from backend.app.forecasting.engine import PriceForecastingEngine
from backend.app.data.mandis_db import BASE_MANDIS

router = APIRouter(prefix="/api/forecasts", tags=["Price Forecasting"])

engine = PriceForecastingEngine()

@router.get("/evaluation")
def get_model_evaluation():
    """
    Returns actual leakage-free rolling-origin backtesting metrics across
    models (LightGBM, Rolling Average, Seasonal Naive, Last Observed),
    sample sizes, evaluation date spans, and horizon MAE/RMSE/WAPE.
    """
    return engine.get_evaluation_results()

@router.get("/{crop_id}", response_model=List[MandiPriceForecast])
def get_crop_forecasts(
    crop_id: str,
    market_id: Optional[str] = Query(None, description="Target mandi code (optional)"),
    horizon: int = Query(3, ge=1, le=14, description="Forecast horizon in days (3 or 7)")
):
    """
    Generates verified 3-day or 7-day price forecasts with empirical 80% prediction intervals,
    model metadata, and data quality warnings.
    """
    target_mandis = [m.id for m in BASE_MANDIS]
    if market_id:
        target_mandis = [market_id]

    forecasts = []
    for m_id in target_mandis:
        fc = engine.get_forecast(commodity_id=crop_id, market_id=m_id, horizon_days=horizon)
        forecasts.append(fc)

    return forecasts
