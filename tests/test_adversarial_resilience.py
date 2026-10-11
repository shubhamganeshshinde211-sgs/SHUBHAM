"""
Adversarial Resilience and Operational Stress Test Suite for AgriRoute Intelligence.
Phase 6: Verifies system robustness under extreme market disruptions, logistics constraints,
perishable biological limits, and optimization boundary conditions.
"""
import pytest
from backend.app.models.schemas import (
    VehicleType,
    OptimizationRequest,
    RiskPolicy,
    MandiInfo,
    CropProfile,
    CropCategory
)
from backend.app.services.economic_engine import (
    AuthoritativeEconomicEngine,
    EconomicCalculationInput
)
from backend.app.services.decay_engine import TransitDecayEngine
from backend.app.services.optimizer import MultiMandiRouteOptimizer
from backend.app.services.allocation_optimizer import MultiMarketAllocationOptimizer
from backend.app.services.risk_engine import RiskAwareDecisionEngine
from backend.app.data.mandis_db import get_crop_by_id, BASE_MANDIS, CROP_CATALOG


# =====================================================================
# 1. MARKET ADVERSARIAL STRESS TESTS
# =====================================================================

def test_sudden_local_price_collapse_redirects_to_regional():
    """
    When the local mandi suffers a severe price crash (e.g., -50%),
    the optimizer must dynamically recommend regional arbitrage to preserve farmer revenue.
    """
    crashed_local = MandiInfo(
        id="m_local_crashed", name="Nashik Local", state="MH", district="Nashik",
        distance_km=25.0, transit_hours=1.0, modal_price_per_kg=12.0,
        min_price_per_kg=10.0, max_price_per_kg=14.0, arrival_volume_mt=400.0,
        daily_price_trend="falling", market_cess_percent=1.0, handling_cost_per_kg=0.7
    )
    stable_regional = MandiInfo(
        id="m_vashi_stable", name="Vashi APMC", state="MH", district="Mumbai",
        distance_km=175.0, transit_hours=4.5, modal_price_per_kg=38.0,
        min_price_per_kg=35.0, max_price_per_kg=42.0, arrival_volume_mt=900.0,
        daily_price_trend="stable", market_cess_percent=1.2, handling_cost_per_kg=0.8
    )

    req = OptimizationRequest(
        crop_id="tomato",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp_celsius=28.0,
        custom_mandis=[crashed_local, stable_regional]
    )
    resp = MultiMandiRouteOptimizer.optimize(req)

    # Regional Vashi should be top-ranked despite 175 km transit
    assert resp.recommended_mandi.mandi_id == "m_vashi_stable"
    assert resp.recommended_mandi.breakdown.net_realization > resp.local_baseline_net
    assert resp.recommended_mandi.breakdown.net_realization > 130000.0


def test_distant_price_spike_arbitrage_trap_prevented():
    """
    Arbitrage Trap Test: A massive price spike in Delhi (+100% at 75 INR/kg, 1280 km)
    must NOT trick the optimizer into sending highly perishable tomatoes in an open truck at 40°C,
    because 32 hours transit in extreme heat causes ~35%+ decay and heavy freight that wipes out profit.
    """
    delhi_spiked = MandiInfo(
        id="m_delhi_spike", name="Delhi Azadpur", state="DL", district="Delhi",
        distance_km=1280.0, transit_hours=32.0, modal_price_per_kg=75.0,
        min_price_per_kg=70.0, max_price_per_kg=80.0, arrival_volume_mt=1500.0,
        daily_price_trend="surging", market_cess_percent=1.5, handling_cost_per_kg=1.0
    )
    vashi_near = MandiInfo(
        id="m_vashi_moderate", name="Vashi APMC", state="MH", district="Mumbai",
        distance_km=175.0, transit_hours=4.5, modal_price_per_kg=38.0,
        min_price_per_kg=35.0, max_price_per_kg=40.0, arrival_volume_mt=900.0,
        daily_price_trend="stable", market_cess_percent=1.2, handling_cost_per_kg=0.8
    )

    req = OptimizationRequest(
        crop_id="tomato",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.OPEN_TRUCK,
        ambient_temp_celsius=40.0,
        custom_mandis=[delhi_spiked, vashi_near]
    )
    resp = MultiMandiRouteOptimizer.optimize(req)

    delhi_res = next(r for r in resp.ranked_routes if r.mandi_id == "m_delhi_spike")
    vashi_res = next(r for r in resp.ranked_routes if r.mandi_id == "m_vashi_moderate")

    # Spoilage in Delhi under open truck at 40°C must be severe (>20%)
    assert delhi_res.transit_loss_fraction > 0.20
    # Net realization for Vashi should outperform Delhi after factoring in ~₹45k freight and spoilage
    assert vashi_res.breakdown.net_realization > delhi_res.breakdown.net_realization
    assert resp.recommended_mandi.mandi_id == "m_vashi_moderate"


def test_depressed_market_negative_margins_warned():
    """
    When market price drops below transport + cess + handling costs (e.g. 2 INR/kg),
    the system correctly reports negative net realization and transparent warnings.
    """
    inp = EconomicCalculationInput(
        quantity_kg=5000.0,
        mandi_price_per_kg=2.0,
        distance_km=200.0,
        transit_loss_fraction=0.08,
        vehicle_type=VehicleType.COVERED_TRUCK,
        market_cess_percent=1.5,
        handling_cost_per_kg=1.0,
        holding_cost_per_hour=100.0,
        holding_wait_hours=2.0
    )
    bd = AuthoritativeEconomicEngine.evaluate_action(inp)
    assert bd.expected_net_realization < 0
    assert bd.net_realization_per_kg < 0
    assert any("negative" in w.lower() for w in bd.assumptions_and_warnings)


def test_identical_net_realization_deterministic_tie_breaking():
    """
    When two mandis have mathematically identical net realization,
    ranking must be deterministic and never fail or crash.
    """
    m1 = MandiInfo(
        id="m_alpha", name="Alpha Mandi", state="MH", district="Alpha",
        distance_km=100.0, transit_hours=3.0, modal_price_per_kg=30.0,
        min_price_per_kg=28.0, max_price_per_kg=32.0, arrival_volume_mt=500.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.8
    )
    m2 = MandiInfo(
        id="m_beta", name="Beta Mandi", state="MH", district="Beta",
        distance_km=100.0, transit_hours=3.0, modal_price_per_kg=30.0,
        min_price_per_kg=28.0, max_price_per_kg=32.0, arrival_volume_mt=500.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.8
    )
    req = OptimizationRequest(
        crop_id="onion",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp_celsius=25.0,
        custom_mandis=[m1, m2]
    )
    resp1 = MultiMandiRouteOptimizer.optimize(req)
    resp2 = MultiMandiRouteOptimizer.optimize(req)

    # Ranking must be identical between runs
    assert resp1.ranked_routes[0].mandi_id == resp2.ranked_routes[0].mandi_id
    assert abs(resp1.ranked_routes[0].breakdown.net_realization - resp1.ranked_routes[1].breakdown.net_realization) < 0.01


# =====================================================================
# 2. LOGISTICS & BIOLOGICAL ADVERSARIAL TESTS
# =====================================================================

def test_shelf_life_expiry_precludes_allocation():
    """
    If total transit + handling time exceeds the crop's base safe shelf life,
    the multi-market LP must strictly exclude that mandi (0 allocation) to prevent catastrophic spoilage.
    """
    # Create an ultra-perishable crop profile with only 10 hours safe shelf life
    ultra_perishable_crop = CropProfile(
        id="spinach_test",
        name="Test Spinach",
        category=CropCategory.HIGH_PERISHABLE,
        base_shelf_life_hours=10.0,
        hourly_decay_rate=0.03,
        temperature_sensitivity=2.0,
        optimal_temp_celsius=8.0,
        moisture_loss_rate_per_hour=0.005,
        description="Ultra-perishable leafy green for boundary test"
    )
    mandi_far = MandiInfo(
        id="m_distant", name="Distant Hub", state="KA", district="Bangalore",
        distance_km=850.0, transit_hours=20.0, modal_price_per_kg=60.0,
        min_price_per_kg=55.0, max_price_per_kg=65.0, arrival_volume_mt=300.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.8,
        average_unloading_wait_hours=4.0
    )

    plan = MultiMarketAllocationOptimizer.solve_allocation(
        crop=ultra_perishable_crop,
        mandis=[mandi_far],
        total_quantity_kg=3000.0,
        vehicle_type=VehicleType.OPEN_TRUCK,
        ambient_temp=35.0,
        mandi_prices={"m_distant": 60.0}
    )

    # Distant Hub requires 24h which exceeds 10h shelf life
    assert len(plan.splits) == 0
    assert plan.unallocated_quantity_kg == 3000.0
    assert "shelf-life" in plan.allocation_rationale.lower()


def test_massive_payload_fleet_scaling():
    """
    When consignment quantity exceeds single-vehicle payload (e.g. 25,000 kg vs 9,000 kg payload),
    freight calculation must properly allocate multiple commercial vehicles (ceil(25000/9000) = 3 trucks).
    """
    cost_single, warn_single = AuthoritativeEconomicEngine.calculate_freight(
        distance_km=200.0,
        quantity_kg=8000.0,
        vehicle_type=VehicleType.COVERED_TRUCK
    )
    cost_heavy, warn_heavy = AuthoritativeEconomicEngine.calculate_freight(
        distance_km=200.0,
        quantity_kg=25000.0,
        vehicle_type=VehicleType.COVERED_TRUCK
    )

    # 25,000 kg requires 3 trucks, cost must be substantially higher than 1 truckload
    assert cost_heavy > 2.5 * cost_single
    assert any("fleet" in w.lower() or "vehicles" in w.lower() or "trucks" in w.lower() for w in warn_heavy)


def test_fuel_surge_shifts_preference_to_closer_markets():
    """
    Under a 2.5x fuel price surge (+150%), long haul freight escalates drastically,
    making nearby markets relatively more attractive.
    """
    crop = CROP_CATALOG["potato"]
    local_mandi = MandiInfo(
        id="m_local", name="Local Mandi", state="MH", district="Local",
        distance_km=40.0, transit_hours=1.5, modal_price_per_kg=24.0,
        min_price_per_kg=22.0, max_price_per_kg=26.0, arrival_volume_mt=300.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.5
    )
    far_mandi = MandiInfo(
        id="m_far", name="Far Mandi", state="GJ", district="Surat",
        distance_km=350.0, transit_hours=8.0, modal_price_per_kg=29.0,
        min_price_per_kg=27.0, max_price_per_kg=31.0, arrival_volume_mt=500.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.5
    )

    req_base = OptimizationRequest(
        crop_id="potato",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp_celsius=25.0,
        fuel_rate_per_km_multiplier=1.0,
        custom_mandis=[local_mandi, far_mandi]
    )
    resp_base = MultiMandiRouteOptimizer.optimize(req_base)

    req_surge = OptimizationRequest(
        crop_id="potato",
        quantity_kg=5000.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp_celsius=25.0,
        fuel_rate_per_km_multiplier=2.5,
        custom_mandis=[local_mandi, far_mandi]
    )
    resp_surge = MultiMandiRouteOptimizer.optimize(req_surge)

    # Calculate net margin spread (Far - Local) under normal vs surged fuel
    spread_base = (
        next(r for r in resp_base.ranked_routes if r.mandi_id == "m_far").breakdown.net_realization -
        next(r for r in resp_base.ranked_routes if r.mandi_id == "m_local").breakdown.net_realization
    )
    spread_surge = (
        next(r for r in resp_surge.ranked_routes if r.mandi_id == "m_far").breakdown.net_realization -
        next(r for r in resp_surge.ranked_routes if r.mandi_id == "m_local").breakdown.net_realization
    )

    # Spread must narrow significantly under high fuel surge
    assert spread_surge < spread_base


def test_reefer_economic_penalty_for_hardy_produce():
    """
    Economic Tradeoff Invariant: For non-perishable produce (e.g. Onion with 720h shelf life),
    hiring an expensive Reefer Cold-Chain vehicle (+4000 base + 7.8/ton-km) yields LOWER
    net realization than a standard Covered truck, proving cold-chain is not wastefully over-recommended.
    """
    crop = CROP_CATALOG["onion"]
    mandi = MandiInfo(
        id="m_vashi", name="Vashi APMC", state="MH", district="Mumbai",
        distance_km=175.0, transit_hours=4.5, modal_price_per_kg=28.0,
        min_price_per_kg=25.0, max_price_per_kg=30.0, arrival_volume_mt=800.0,
        daily_price_trend="stable", market_cess_percent=1.2, handling_cost_per_kg=0.75
    )

    loss_cov, _, _ = TransitDecayEngine.calculate_transit_loss(crop, mandi, VehicleType.COVERED_TRUCK, 30.0)
    loss_ref, _, _ = TransitDecayEngine.calculate_transit_loss(crop, mandi, VehicleType.REEFER_COLD, 30.0)

    inp_cov = EconomicCalculationInput(
        quantity_kg=6000.0, mandi_price_per_kg=28.0, distance_km=175.0,
        transit_loss_fraction=loss_cov, vehicle_type=VehicleType.COVERED_TRUCK,
        market_cess_percent=1.2, handling_cost_per_kg=0.75, holding_cost_per_hour=100.0, holding_wait_hours=2.0
    )
    inp_ref = EconomicCalculationInput(
        quantity_kg=6000.0, mandi_price_per_kg=28.0, distance_km=175.0,
        transit_loss_fraction=loss_ref, vehicle_type=VehicleType.REEFER_COLD,
        market_cess_percent=1.2, handling_cost_per_kg=0.75, holding_cost_per_hour=100.0, holding_wait_hours=2.0
    )

    bd_cov = AuthoritativeEconomicEngine.evaluate_action(inp_cov)
    bd_ref = AuthoritativeEconomicEngine.evaluate_action(inp_ref)

    # Covered truck must generate higher net realization for Onion
    assert bd_cov.expected_net_realization > bd_ref.expected_net_realization
    assert bd_ref.transport_expense > bd_cov.transport_expense


# =====================================================================
# 3. OPTIMIZATION BOUNDARY & MASS CONSERVATION TESTS
# =====================================================================

def test_mass_conservation_with_unallocated_produce():
    """
    Mass conservation invariant must strictly hold even when market capacity limits
    or operational constraints leave produce unallocated:
    initial_quantity = sum(allocated_splits) + unallocated_quantity
                     = (sold + physical_loss) + unallocated_quantity
    """
    crop = CROP_CATALOG["tomato"]
    # Mandi with tiny arrival volume (10 MT) -> 12% absorption = 1.2 MT = 1,200 kg
    small_mandi = MandiInfo(
        id="m_tiny", name="Tiny Mandi", state="MH", district="Rural",
        distance_km=30.0, transit_hours=1.0, modal_price_per_kg=32.0,
        min_price_per_kg=30.0, max_price_per_kg=34.0, arrival_volume_mt=10.0,
        daily_price_trend="stable", market_cess_percent=1.0, handling_cost_per_kg=0.6
    )

    initial_qty = 20000.0  # Large quantity
    plan = MultiMarketAllocationOptimizer.solve_allocation(
        crop=crop,
        mandis=[small_mandi],
        total_quantity_kg=initial_qty,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=26.0,
        mandi_prices={"m_tiny": 32.0}
    )

    allocated_qty = sum(s.allocated_quantity_kg for s in plan.splits)
    assert abs(initial_qty - (allocated_qty + plan.unallocated_quantity_kg)) < 0.01
    assert plan.total_crop_quantity_kg == initial_qty


def test_zero_quantity_guardrails():
    """
    Zero quantity input must return a clean, unallocated plan without mathematical or runtime errors.
    """
    crop = CROP_CATALOG["tomato"]
    mandis = BASE_MANDIS[:2]
    plan = MultiMarketAllocationOptimizer.solve_allocation(
        crop=crop,
        mandis=mandis,
        total_quantity_kg=0.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=25.0,
        mandi_prices={m.id: 30.0 for m in mandis}
    )
    assert plan.total_net_realization == 0.0
    assert plan.unallocated_quantity_kg == 0.0
    assert len(plan.splits) == 0


# =====================================================================
# 4. RISK MEASURE MATHEMATICAL PROPERTIES
# =====================================================================

def test_risk_scenarios_strictly_penalize_downside():
    """
    Verifies that stress-test scenarios (Bear Market -15%, Diesel +25%, Delay/Heat +50%)
    consistently calculate downside impact without double-counting or inflating profits.
    """
    crop = CROP_CATALOG["tomato"]
    mandi = BASE_MANDIS[0]

    profile = RiskAwareDecisionEngine.evaluate_mandi_scenarios(
        crop=crop,
        mandi=mandi,
        quantity_kg=5000.0,
        base_price=35.0,
        vehicle_type=VehicleType.COVERED_TRUCK,
        ambient_temp=30.0,
        fuel_multiplier=1.0,
        price_lower_bound=28.0,
        price_upper_bound=42.0,
        risk_policy=RiskPolicy.BALANCED,
        local_expected_net=120000.0
    )

    base_scen = next(s for s in profile.scenarios if s.scenario_id == "expected")
    bear_scen = next(s for s in profile.scenarios if s.scenario_id == "bear_market")
    diesel_scen = next(s for s in profile.scenarios if s.scenario_id == "high_freight")
    delay_scen = next(s for s in profile.scenarios if s.scenario_id == "severe_spoilage")

    # Bear price must yield lower net than base
    assert bear_scen.net_realization < base_scen.net_realization
    # Diesel spike must yield lower net than base
    assert diesel_scen.net_realization < base_scen.net_realization
    # Delay and heat must yield lower net than base
    assert delay_scen.net_realization < base_scen.net_realization

    # Downside shortfall (downside_var_90_inr) must be positive and bounded by gross potential
    assert profile.downside_var_90_inr > 0
    assert profile.downside_var_90_inr < 5000.0 * 35.0
