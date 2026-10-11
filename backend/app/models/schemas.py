"""
Pydantic data models for AgriRoute Intelligence.
"""
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field

class VehicleType(str, Enum):
    OPEN_TRUCK = "open_truck"
    COVERED_TRUCK = "covered_truck"
    REEFER_COLD = "reefer_cold"

class CropCategory(str, Enum):
    HIGH_PERISHABLE = "high_perishable"
    SEMI_PERISHABLE = "semi_perishable"
    DURABLE_GRAIN = "durable_grain"

class CropProfile(BaseModel):
    id: str
    name: str
    category: CropCategory
    base_shelf_life_hours: float
    hourly_decay_rate: float = Field(..., description="Base fractional decay rate per hour at 25C")
    temperature_sensitivity: float = Field(..., description="Multiplier per 5C above optimal storage")
    optimal_temp_celsius: float
    moisture_loss_rate_per_hour: float = Field(default=0.001)
    description: str

class MandiInfo(BaseModel):
    id: str
    name: str
    state: str
    district: str
    distance_km: float
    transit_hours: float
    modal_price_per_kg: float
    min_price_per_kg: float
    max_price_per_kg: float
    arrival_volume_mt: float
    daily_price_trend: str = Field(..., description="'rising', 'falling', or 'stable'")
    market_cess_percent: float = Field(..., description="APMC market fee percentage (e.g. 1.5%)")
    handling_cost_per_kg: float = Field(..., description="Unloading, weighing, and sorting cost")
    holding_cost_per_hour: float = Field(default=0.0, description="Holding or yard parking fees per hour")
    average_unloading_wait_hours: float = Field(default=1.5)
    road_condition_index: float = Field(default=1.0, description="1.0 normal highway, >1.0 rough road causing bruising")

class RealizationInput(BaseModel):
    quantity_kg: float = Field(gt=0, description="Total crop quantity in kilograms")
    price_per_kg: float = Field(ge=0, description="Selling price per kilogram at destination market")
    loss_fraction: float = Field(ge=0, le=1, description="Fraction of goods lost during transit/spoilage (0 to 1)")
    transport_cost: float = Field(ge=0, description="Total transportation cost")
    handling_cost: float = Field(ge=0, description="Loading/unloading and handling costs")
    holding_cost: float = Field(ge=0, default=0, description="Storage/warehousing costs")
    market_cost: float = Field(ge=0, default=0, description="Mandi/market fees and commissions")

class RealizationBreakdown(BaseModel):
    gross_revenue: float
    saleable_quantity_kg: float
    spoilage_quantity_kg: float
    spoilage_value_loss: float
    transport_cost: float
    handling_cost: float
    market_cess_cost: float
    holding_cost: float
    total_logistics_cost: float
    net_realization: float
    net_per_kg: float
    profit_margin_percent: float

class RiskPolicy(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    RETURN_SEEKING = "return_seeking"

class ScenarioEvaluationSchema(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    price_factor: float
    freight_factor: float
    decay_factor: float
    effective_price_per_kg: float
    transit_loss_fraction: float
    net_realization: float
    net_per_kg: float
    profit_margin_percent: float
    variance_versus_expected_inr: float
    is_downside: bool

class MandiRiskProfileSchema(BaseModel):
    mandi_id: str
    mandi_name: str
    expected_net_realization: float
    risk_adjusted_score: float
    risk_policy: str
    scenarios: List[ScenarioEvaluationSchema]
    downside_var_90_inr: float
    max_drawdown_versus_local_inr: float
    downside_risk_ratio: float
    is_resilient: bool
    policy_explanation: str

class AllocationSplitItem(BaseModel):
    mandi_id: str
    mandi_name: str
    state: str
    allocated_quantity_kg: float
    allocated_percentage: float
    effective_price_per_kg: float
    distance_km: float
    transit_loss_fraction: float
    net_realization: float
    net_per_kg: float
    assigned_vehicles_count: int
    vehicle_type: VehicleType

class PolicyBenchmarkItem(BaseModel):
    policy_name: str
    policy_description: str
    allocated_destinations: List[str]
    total_net_realization: float
    net_per_kg: float
    total_spoilage_kg: float
    total_freight_cost: float
    variance_versus_local_inr: float
    variance_versus_local_percent: float
    is_recommended: bool = False

class MultiMarketAllocationPlanSchema(BaseModel):
    total_crop_quantity_kg: float
    unallocated_quantity_kg: float
    splits: List[AllocationSplitItem]
    total_gross_revenue: float
    total_freight_cost: float
    total_handling_cost: float
    total_market_cess: float
    total_holding_cost: float
    total_net_realization: float
    average_net_per_kg: float
    total_spoilage_kg: float
    benchmarks: List[PolicyBenchmarkItem]
    allocation_rationale: str

class OptimizationRequest(BaseModel):
    origin_name: str = Field(default="Nashik Farm Cluster")
    crop_id: str = Field(default="tomato")
    quantity_kg: float = Field(gt=0, default=5000.0)
    vehicle_type: VehicleType = Field(default=VehicleType.COVERED_TRUCK)
    ambient_temp_celsius: float = Field(default=32.0, ge=-10, le=55)
    fuel_rate_per_km_multiplier: float = Field(default=1.0, ge=0.5, le=3.0)
    custom_mandis: Optional[List[MandiInfo]] = None
    forecast_horizon_days: Optional[int] = Field(default=None, description="Optional 3 or 7 day horizon for forecast-aware dispatch")
    decision_policy: Optional[str] = Field(default="immediate", description="'immediate' or 'forecast_aware'")
    risk_policy: Optional[str] = Field(default="balanced", description="'conservative', 'balanced', or 'return_seeking'")
    allow_multi_market_split: Optional[bool] = Field(default=True, description="Enable LP solver for multi-mandi produce split")

class MandiRouteResult(BaseModel):
    mandi_id: str
    mandi_name: str
    state: str
    distance_km: float
    transit_hours: float
    unloading_wait_hours: float
    total_duration_hours: float
    vehicle_type: VehicleType
    transit_loss_fraction: float
    decay_explanation: str
    price_per_kg: float
    breakdown: RealizationBreakdown
    freshness_index_percent: float
    is_recommended: bool = False
    rank: int = 1
    recommendation_badge: str = ""
    risk_level: str = "Low"
    
    # Forecast-aware extension fields
    observed_price_per_kg: Optional[float] = None
    forecasted_price_per_kg: Optional[float] = None
    price_lower_bound: Optional[float] = None
    price_upper_bound: Optional[float] = None
    forecast_horizon_days: Optional[int] = None
    forecast_status: Optional[str] = None
    data_mode: Optional[str] = None
    timing_recommendation: Optional[str] = None
    net_realization_forecast: Optional[float] = None

    # Risk-aware & scenario fields
    risk_adjusted_score: Optional[float] = None
    downside_var_90_inr: Optional[float] = None
    is_resilient: Optional[bool] = None
    scenarios: Optional[List[ScenarioEvaluationSchema]] = None
    risk_policy_explanation: Optional[str] = None

class OptimizationResponse(BaseModel):
    origin_name: str
    crop: CropProfile
    quantity_kg: float
    vehicle_type: VehicleType
    ambient_temp_celsius: float
    ranked_routes: List[MandiRouteResult]
    recommended_mandi: MandiRouteResult
    insights: List[str]
    active_data_mode: str = "HISTORICAL_DATA"
    forecast_applied: bool = False
    
    # Phase 5 additions
    allocation_plan: Optional[MultiMarketAllocationPlanSchema] = None
    risk_policy_applied: str = "balanced"
    local_baseline_net: float = 0.0

