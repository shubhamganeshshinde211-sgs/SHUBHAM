"""
Economic Consistency and Logistics Optimization Unit Tests.
Verifies economic invariants, monotonicity, and no double-counting of spoilage.
"""
import pytest
from backend.app.models.schemas import OptimizationRequest, VehicleType, MandiInfo
from backend.app.services.optimizer import MultiMandiRouteOptimizer
from backend.app.services.decay_engine import TransitDecayEngine
from backend.app.data.mandis_db import CROP_CATALOG

def test_freight_monotonicity():
    # Increasing distance strictly increases freight
    cost_short = MultiMandiRouteOptimizer.calculate_freight_cost(
        distance_km=50.0, quantity_kg=5000.0, vehicle_type=VehicleType.COVERED_TRUCK
    )
    cost_long = MultiMandiRouteOptimizer.calculate_freight_cost(
        distance_km=250.0, quantity_kg=5000.0, vehicle_type=VehicleType.COVERED_TRUCK
    )
    assert cost_long > cost_short

    # Increasing fuel multiplier strictly increases freight
    cost_base = MultiMandiRouteOptimizer.calculate_freight_cost(
        distance_km=100.0, quantity_kg=5000.0, vehicle_type=VehicleType.COVERED_TRUCK, fuel_multiplier=1.0
    )
    cost_surge = MultiMandiRouteOptimizer.calculate_freight_cost(
        distance_km=100.0, quantity_kg=5000.0, vehicle_type=VehicleType.COVERED_TRUCK, fuel_multiplier=1.4
    )
    assert cost_surge > cost_base

def test_decay_monotonicity_with_temperature():
    crop = CROP_CATALOG["tomato"]
    mandi = MandiInfo(
        id="m1", name="M1", state="MH", district="D1",
        distance_km=150.0, transit_hours=4.0, modal_price_per_kg=35.0,
        min_price_per_kg=30.0, max_price_per_kg=40.0, arrival_volume_mt=100.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.8
    )

    loss_cool, fresh_cool, _ = TransitDecayEngine.calculate_transit_loss(
        crop=crop, mandi=mandi, vehicle_type=VehicleType.COVERED_TRUCK, ambient_temp_celsius=20.0
    )
    loss_hot, fresh_hot, _ = TransitDecayEngine.calculate_transit_loss(
        crop=crop, mandi=mandi, vehicle_type=VehicleType.COVERED_TRUCK, ambient_temp_celsius=42.0
    )

    assert loss_hot > loss_cool
    assert fresh_cool > fresh_hot

def test_higher_headline_price_can_yield_lower_net_realization():
    """
    Arbitrage invariant: A far distant market with a high nominal price
    (e.g. Delhi at ₹52/kg, 1250 km) must yield lower net realization than a nearby
    market (e.g. Vashi at ₹38.5/kg, 175 km) for highly perishable tomatoes in an open truck.
    """
    req = OptimizationRequest(
        crop_id="tomato",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.OPEN_TRUCK,
        ambient_temp_celsius=35.0
    )
    resp = MultiMandiRouteOptimizer.optimize(req)

    vashi = next((r for r in resp.ranked_routes if "vashi" in r.mandi_id), None)
    delhi = next((r for r in resp.ranked_routes if "azadpur" in r.mandi_id), None)

    assert vashi is not None and delhi is not None
    assert delhi.price_per_kg > vashi.price_per_kg  # Headline price is higher
    assert vashi.breakdown.net_realization > delhi.breakdown.net_realization # But net profit is higher at Vashi!

def test_no_double_counting_spoilage():
    req = OptimizationRequest(crop_id="tomato", quantity_kg=5000.0)
    resp = MultiMandiRouteOptimizer.optimize(req)
    r = resp.ranked_routes[0]

    # saleable_quantity + spoilage_quantity must strictly equal initial quantity
    total_qty = r.breakdown.saleable_quantity_kg + r.breakdown.spoilage_quantity_kg
    assert pytest.approx(total_qty, rel=1e-3) == 5000.0

    # Net realization must equal gross revenue minus logistics deductions
    expected_net = r.breakdown.gross_revenue - r.breakdown.total_logistics_cost
    assert pytest.approx(r.breakdown.net_realization, rel=1e-2) == expected_net
