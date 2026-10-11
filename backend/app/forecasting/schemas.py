"""
Forecasting Pydantic Schemas and Evaluation Metric Models.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class ForecastHorizon(int, Enum):
    HORIZON_3D = 3
    HORIZON_7D = 7

class ForecastStatus(str, Enum):
    OPTIMAL_MODEL = "OPTIMAL_MODEL"           # High-confidence model prediction
    BASELINE_FALLBACK = "BASELINE_FALLBACK"   # Baseline selected because ML was inferior or uncalibrated
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"   # Not enough historical observations
    STALE_INPUT = "STALE_INPUT"               # Latest observation is older than 5 days

class MandiPriceForecast(BaseModel):
    commodity_id: str
    commodity_name: str
    market_id: str
    market_name: str
    forecast_generation_time: datetime
    latest_observation_date: date
    latest_observed_price: float
    target_date: date
    horizon_days: int
    predicted_modal_price: float = Field(..., ge=0)
    lower_bound_price: Optional[float] = None
    upper_bound_price: Optional[float] = None
    prediction_interval_confidence: Optional[float] = 0.80
    model_name: str
    model_version: str = "1.0.0"
    historical_observations_count: int
    data_freshness_days: int
    forecast_status: ForecastStatus
    warning_notes: Optional[str] = None

class HorizonEvaluationMetrics(BaseModel):
    horizon_days: int
    evaluated_observations_count: int
    mae: float
    rmse: float
    wape: float
    directional_accuracy: Optional[float] = None
    interval_coverage: Optional[float] = None

class ModelComparison(BaseModel):
    model_name: str
    is_best_performing: bool = False
    metrics_3d: HorizonEvaluationMetrics
    metrics_7d: HorizonEvaluationMetrics

class CommodityEvaluationReport(BaseModel):
    commodity_id: str
    evaluation_date_range: Dict[str, str]
    models: List[ModelComparison]
    recommended_model_3d: str
    recommended_model_7d: str
    audited_at: datetime

class FullEvaluationSummary(BaseModel):
    audited_at: datetime
    total_evaluated_samples: int
    commodities: Dict[str, CommodityEvaluationReport]
