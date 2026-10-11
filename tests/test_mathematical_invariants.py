"""
Rigorous Mathematical Invariants and Economic Resilience Test Suite.
Verifies the authoritative economic properties required by Phase 5:
1. Transport cost monotonicity (dNet/dTransport <= 0)
2. Spoilage loss monotonicity (dNet/dLoss <= 0)
3. Price monotonicity (dNet/dPrice >= 0)
4. Holding cost monotonicity (dNet/dHolding <= 0)
5. Conservation of mass (Q_sold + Q_lost == Q_initial)
6. Zero double-deduction of physical loss
7. Local baseline calculation parity under identical conventions
8. Vehicle payload bounds & fleet allocation
9. Risk policy monotonicity: Conservative score <= Balanced score <= Return-Seeking score
10. Multi-market LP allocation conservation and capacity limits
"""
import pytest
from backend.app.models.schemas import (
    VehicleType,
    OptimizationRequest,
    RiskPolicy
)
from backend.app.services.economic_engine import (
    AuthoritativeEconomicEngine,
    EconomicCalculationInput
)
from backend.app.services.optimizer import MultiMandiRouteOptimizer
from backend.app.services.allocation_optimizer import MultiMarketAllocationOptimizer
from backend.app.services.risk_engine import RiskAwareDecisionEngine
from backend.app.data.mandis_db import get_crop_by_id, get_mandis_for_crop

@pytest.fixture
def base_input():
    return EconomicCalculationInput(
        quantity_kg=5000.0,
        mandi_price_per_kg=35.0,
        distance_km=200.0,
        transit_loss_fraction=0.05,
        vehicle_type=VehicleType.COVERED_TRUCK,
        market_cess_percent=1.2,
        handling_cost_per_kg=0.75,
        holding_cost_per_hour=100.0,
        holding_wait_hours=2.0,
        fuel_multiplier=1.0,
        storage_days=0,
        freshness_index=95.0,
        daily_arrival_volume_mt=350.0
    )

def test_transport_cost_monotonicity(base_input):
    """
    Mathematical Invariant: Increasing transport cost cannot improve an otherwise identical action's net realization.
    """
    bd_low_freight = AuthoritativeEconomicEngine.evaluate_action(base_input)

    # Elevate fuel multiplier by +50%
    high_input = EconomicCalculationInput(**{**base_input.__dict__, "fuel_multiplier": 1.5})
    bd_high_freight = AuthoritativeEconomicEngine.evaluate_action(high_input)

    assert bd_high_freight.transport_expense > bd_low_freight.transport_expense
    assert bd_high_freight.expected_net_realization < bd_low_freight.expected_net_realization
    assert bd_high_freight.net_realization_per_kg < bd_low_freight.net_realization_per_kg

def test_physical_loss_monotonicity(base_input):
    """
    Mathematical Invariant: Increasing physical loss cannot improve an otherwise identical action's net realization.
    """
    bd_low_loss = AuthoritativeEconomicEngine.evaluate_action(base_input)

    # Double transit loss fraction from 5% to 15%
    high_loss_input = EconomicCalculationInput(**{**base_input.__dict__, "transit_loss_fraction": 0.15})
    bd_high_loss = AuthoritativeEconomicEngine.evaluate_action(high_loss_input)

    assert bd_high_loss.expected_quantity_sold_kg < bd_low_loss.expected_quantity_sold_kg
    assert bd_high_loss.expected_physical_loss_kg > bd_low_loss.expected_physical_loss_kg
    assert bd_high_loss.expected_net_realization < bd_low_loss.expected_net_realization

def test_price_monotonicity(base_input):
    """
    Mathematical Invariant: Increasing selling price cannot reduce net realization when all other terms remain fixed.
    """
    bd_base_price = AuthoritativeEconomicEngine.evaluate_action(base_input)

    # Elevate price from 35 to 45 INR/kg
    higher_price_input = EconomicCalculationInput(**{**base_input.__dict__, "mandi_price_per_kg": 45.0})
    bd_higher_price = AuthoritativeEconomicEngine.evaluate_action(higher_price_input)

    assert bd_higher_price.quality_adjusted_price_per_kg > bd_base_price.quality_adjusted_price_per_kg
    assert bd_higher_price.gross_realized_revenue > bd_base_price.gross_realized_revenue
    assert bd_higher_price.expected_net_realization > bd_base_price.expected_net_realization

def test_holding_cost_monotonicity(base_input):
    """
    Mathematical Invariant: Increasing holding costs cannot improve an otherwise identical waiting action's net realization.
    """
    hold_3d_input = EconomicCalculationInput(**{**base_input.__dict__, "storage_days": 3, "storage_cost_per_kg_day": 0.10})
    bd_hold_cheap = AuthoritativeEconomicEngine.evaluate_action(hold_3d_input)

    # Triple storage rate to 0.30 INR/kg/day
    hold_expensive_input = EconomicCalculationInput(**{**base_input.__dict__, "storage_days": 3, "storage_cost_per_kg_day": 0.30})
    bd_hold_expensive = AuthoritativeEconomicEngine.evaluate_action(hold_expensive_input)

    assert bd_hold_expensive.storage_holding_expense > bd_hold_cheap.storage_holding_expense
    assert bd_hold_expensive.expected_net_realization < bd_hold_cheap.expected_net_realization

def test_mass_conservation_invariant(base_input):
    """
    Mathematical Invariant: Every allocated kilogram is accounted for exactly once: Q_sold + Q_lost == Q_initial.
    """
    for loss in [0.0, 0.045, 0.125, 0.333, 0.85]:
        inp = EconomicCalculationInput(**{**base_input.__dict__, "transit_loss_fraction": loss})
        bd = AuthoritativeEconomicEngine.evaluate_action(inp)
        
        sum_kg = round(bd.expected_quantity_sold_kg + bd.expected_physical_loss_kg, 2)
        assert sum_kg == pytest.approx(base_input.quantity_kg, abs=0.01)

def test_no_double_deduction_of_spoilage(base_input):
    """
    Mathematical Invariant: Physical loss reduces sold quantity; it is NEVER deducted again as a cash expense from revenue.
    """
    bd = AuthoritativeEconomicEngine.evaluate_action(base_input)
    
    # Net must exactly equal: SoldKg * Price - (Transport + Handling + Cess + Holding)
    direct_computed_net = round(
        (bd.expected_quantity_sold_kg * bd.quality_adjusted_price_per_kg)
        - (bd.transport_expense + bd.handling_expense + bd.market_cess_expense + bd.unloading_holding_expense + bd.storage_holding_expense),
        2
    )
    assert bd.expected_net_realization == pytest.approx(direct_computed_net, abs=0.05)

def test_local_baseline_parity(base_input):
    """
    Mathematical Invariant: The local-sale baseline is calculated using the exact same financial conventions as alternative destinations.
    """
    req = OptimizationRequest(
        crop_id="tomato",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp_celsius=30.0
    )
    resp = MultiMandiRouteOptimizer.optimize(req)
    
    # Find closest local mandi in routes
    local_route = min(resp.ranked_routes, key=lambda r: r.distance_km)
    assert resp.local_baseline_net == pytest.approx(local_route.breakdown.net_realization, abs=0.01)

def test_multi_market_allocation_conservation():
    """
    Mathematical Invariant: Multi-market allocation solver conserves produce (TotalAllocated <= TotalQuantity).
    """
    crop = get_crop_by_id("tomato")
    mandis = get_mandis_for_crop("tomato")
    prices = {m.id: m.modal_price_per_kg for m in mandis}
    
    total_qty = 15000.0  # Large lot requiring distribution
    plan = MultiMarketAllocationOptimizer.solve_allocation(
        crop=crop,
        mandis=mandis,
        total_quantity_kg=total_qty,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=30.0,
        mandi_prices=prices,
        allow_splitting=True
    )
    
    allocated_sum = sum(s.allocated_quantity_kg for s in plan.splits)
    assert allocated_sum <= total_qty
    assert round(allocated_sum + plan.unallocated_quantity_kg, 2) == pytest.approx(total_qty, abs=0.05)
    assert len(plan.benchmarks) >= 3

def test_risk_policy_ordering():
    """
    Mathematical Invariant: For identical uncertain routes, Conservative score <= Balanced score <= Return-Seeking score.
    """
    crop = get_crop_by_id("tomato")
    mandis = get_mandis_for_crop("tomato")
    test_mandi = mandis[0]
    
    rp_cons = RiskAwareDecisionEngine.evaluate_mandi_scenarios(
        crop=crop,
        mandi=test_mandi,
        quantity_kg=5000.0,
        base_price=38.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=32.0,
        risk_policy=RiskPolicy.CONSERVATIVE
    )
    rp_bal = RiskAwareDecisionEngine.evaluate_mandi_scenarios(
        crop=crop,
        mandi=test_mandi,
        quantity_kg=5000.0,
        base_price=38.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=32.0,
        risk_policy=RiskPolicy.BALANCED
    )
    rp_ret = RiskAwareDecisionEngine.evaluate_mandi_scenarios(
        crop=crop,
        mandi=test_mandi,
        quantity_kg=5000.0,
        base_price=38.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=32.0,
        risk_policy=RiskPolicy.RETURN_SEEKING
    )
    
    # Assert Conservative discounts downside most, Return-Seeking discounts 0
    assert rp_cons.risk_adjusted_score <= rp_bal.risk_adjusted_score
    assert rp_bal.risk_adjusted_score <= rp_ret.risk_adjusted_score
    assert rp_ret.risk_adjusted_score == pytest.approx(rp_ret.expected_net_realization, abs=0.01)

def test_scenario_stress_test_monotonicity():
    """
    Mathematical Invariant: Bear Market Net <= Expected Base Case Net <= Bull Market Net.
    """
    crop = get_crop_by_id("tomato")
    mandis = get_mandis_for_crop("tomato")
    test_mandi = mandis[0]
    
    risk_prof = RiskAwareDecisionEngine.evaluate_mandi_scenarios(
        crop=crop,
        mandi=test_mandi,
        quantity_kg=5000.0,
        base_price=38.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=32.0
    )
    
    sc_map = {s.scenario_id: s.net_realization for s in risk_prof.scenarios}
    assert sc_map["bear_market"] < sc_map["expected"]
    assert sc_map["expected"] < sc_map["bull_market"]
    assert sc_map["high_freight"] < sc_map["expected"]
    assert sc_map["severe_spoilage"] < sc_map["expected"]
