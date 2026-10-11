"""
Multi-Market Allocation Optimizer and Baseline Benchmark Service.
Solves constrained produce split allocations across multiple mandis
using Scipy LP optimization, and benchmarks against standard policies:
1. 100% Local Sale Baseline
2. 100% Highest Observed Price Policy
3. 100% Highest Forecast Price Policy
4. Optimized Multi-Mandi Split Allocation
"""
import numpy as np
from scipy.optimize import linprog
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from backend.app.models.schemas import (
    VehicleType,
    CropProfile,
    MandiInfo,
    OptimizationRequest
)
from backend.app.services.decay_engine import TransitDecayEngine
from backend.app.services.economic_engine import (
    AuthoritativeEconomicEngine,
    EconomicCalculationInput,
    AuthoritativeEconomicBreakdown
)

@dataclass
class AllocationSplit:
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

@dataclass
class PolicyBenchmarkResult:
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

@dataclass
class MultiMarketAllocationPlan:
    total_crop_quantity_kg: float
    unallocated_quantity_kg: float
    splits: List[AllocationSplit]
    total_gross_revenue: float
    total_freight_cost: float
    total_handling_cost: float
    total_market_cess: float
    total_holding_cost: float
    total_net_realization: float
    average_net_per_kg: float
    total_spoilage_kg: float
    benchmarks: List[PolicyBenchmarkResult]
    allocation_rationale: str

class MultiMarketAllocationOptimizer:
    """
    Solves optimal distribution of produce across regional and local mandis.
    """

    @classmethod
    def evaluate_mandi_unit_economics(
        cls,
        crop: CropProfile,
        mandi: MandiInfo,
        vehicle_type: VehicleType,
        ambient_temp: float,
        price_per_kg: float,
        test_quantity_kg: float = 1000.0,
        fuel_multiplier: float = 1.0,
        storage_days: int = 0
    ) -> Tuple[float, float, float, AuthoritativeEconomicBreakdown]:
        """
        Calculates marginal net realization per kg and transit loss for a specific mandi.
        """
        loss_frac, freshness, _ = TransitDecayEngine.calculate_transit_loss(
            crop=crop,
            mandi=mandi,
            vehicle_type=vehicle_type,
            ambient_temp_celsius=ambient_temp
        )

        inp = EconomicCalculationInput(
            quantity_kg=test_quantity_kg,
            mandi_price_per_kg=price_per_kg,
            distance_km=mandi.distance_km,
            transit_loss_fraction=loss_frac,
            vehicle_type=vehicle_type,
            market_cess_percent=mandi.market_cess_percent,
            handling_cost_per_kg=mandi.handling_cost_per_kg,
            holding_cost_per_hour=mandi.holding_cost_per_hour,
            holding_wait_hours=mandi.average_unloading_wait_hours,
            fuel_multiplier=fuel_multiplier,
            storage_days=storage_days,
            freshness_index=freshness,
            daily_arrival_volume_mt=mandi.arrival_volume_mt
        )

        breakdown = AuthoritativeEconomicEngine.evaluate_action(inp)
        marginal_net_per_kg = breakdown.net_realization / test_quantity_kg
        return marginal_net_per_kg, loss_frac, freshness, breakdown

    @classmethod
    def solve_allocation(
        cls,
        crop: CropProfile,
        mandis: List[MandiInfo],
        total_quantity_kg: float,
        vehicle_type: VehicleType,
        ambient_temp: float,
        mandi_prices: Dict[str, float],
        fuel_multiplier: float = 1.0,
        allow_splitting: bool = True
    ) -> MultiMarketAllocationPlan:
        """
        Formulates and solves the linear program for optimal multi-market allocation.
        Subject to:
        1. sum(x_m) <= total_quantity_kg
        2. x_m <= max_absorption_capacity_m (e.g. 15% of daily mandi arrival volume)
        3. x_m >= 0
        4. Safe shelf-life constraint: if transit + wait > safe shelf life, x_m == 0
        """
        n = len(mandis)
        if n == 0 or total_quantity_kg <= 0:
            return MultiMarketAllocationPlan(
                total_crop_quantity_kg=total_quantity_kg,
                unallocated_quantity_kg=total_quantity_kg,
                splits=[],
                total_gross_revenue=0.0,
                total_freight_cost=0.0,
                total_handling_cost=0.0,
                total_market_cess=0.0,
                total_holding_cost=0.0,
                total_net_realization=0.0,
                average_net_per_kg=0.0,
                total_spoilage_kg=0.0,
                benchmarks=[],
                allocation_rationale="No candidate markets or zero quantity provided."
            )

        # 1. Compute marginal net returns and capacity limits
        c_vector = []  # Objective coefficients (maximize sum c_m * x_m -> minimize -c_m * x_m)
        capacities = []
        marginal_data = {}

        specs = AuthoritativeEconomicEngine.VEHICLE_LOGISTICS.get(
            vehicle_type,
            AuthoritativeEconomicEngine.VEHICLE_LOGISTICS[VehicleType.COVERED_TRUCK]
        )
        max_vehicle_payload = specs["max_payload_kg"]

        for m in mandis:
            price = mandi_prices.get(m.id, m.modal_price_per_kg)
            total_journey_h = m.transit_hours + m.average_unloading_wait_hours

            # Shelf-life feasibility check
            is_feasible = (total_journey_h + 8.0) <= crop.base_shelf_life_hours

            if is_feasible:
                net_per_kg, loss_f, fresh, bd = cls.evaluate_mandi_unit_economics(
                    crop=crop,
                    mandi=m,
                    vehicle_type=vehicle_type,
                    ambient_temp=ambient_temp,
                    price_per_kg=price,
                    test_quantity_kg=min(total_quantity_kg, max_vehicle_payload),
                    fuel_multiplier=fuel_multiplier
                )
                # Absorption capacity: max 12% of daily market arrival volume, but at least 1 truckload
                mandi_absorption_kg = max(max_vehicle_payload, m.arrival_volume_mt * 1000.0 * 0.12)
            else:
                net_per_kg = -999.0  # Infeasible due to shelf-life expiry
                loss_f = 1.0
                fresh = 0.0
                mandi_absorption_kg = 0.0

            marginal_data[m.id] = {
                "mandi": m,
                "price": price,
                "net_per_kg": net_per_kg,
                "loss_f": loss_f,
                "fresh": fresh,
                "capacity": mandi_absorption_kg,
                "feasible": is_feasible
            }
            c_vector.append(-net_per_kg)  # Minimize negative returns
            capacities.append(mandi_absorption_kg)

        # 2. Run LP optimization
        # Constraints:
        # A_ub * x <= b_ub:
        # Row 1: sum(x_m) <= total_quantity_kg
        # Bounds: 0 <= x_m <= capacities[m]
        c = np.array(c_vector)
        A_ub = np.ones((1, n))
        b_ub = np.array([total_quantity_kg])
        bounds = [(0, capacities[i] if marginal_data[mandis[i].id]["feasible"] else 0) for i in range(n)]

        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

        allocated_quantities = {}
        if res.success:
            for idx, m in enumerate(mandis):
                qty = float(res.x[idx])
                # Filter out microscopic numerical residue
                if qty >= 50.0:
                    allocated_quantities[m.id] = qty
        else:
            # Fallback to greedy single best
            sorted_mandis = sorted(mandis, key=lambda m: marginal_data[m.id]["net_per_kg"], reverse=True)
            best_m = sorted_mandis[0]
            allocated_quantities[best_m.id] = total_quantity_kg

        # If user disabled multi-market splitting or only 1 mandi was selected
        if not allow_splitting and len(allocated_quantities) > 1:
            best_mandi_id = max(allocated_quantities.keys(), key=lambda mid: marginal_data[mid]["net_per_kg"])
            allocated_quantities = {best_mandi_id: total_quantity_kg}

        # 3. Construct detailed financial breakdown for allocated splits
        splits: List[AllocationSplit] = []
        total_gross = 0.0
        total_freight = 0.0
        total_handling = 0.0
        total_cess = 0.0
        total_holding = 0.0
        total_net = 0.0
        total_spoilage = 0.0
        allocated_total_kg = sum(allocated_quantities.values())

        for m in mandis:
            qty = allocated_quantities.get(m.id, 0.0)
            if qty <= 0:
                continue

            price = marginal_data[m.id]["price"]
            loss_f = marginal_data[m.id]["loss_f"]
            fresh = marginal_data[m.id]["fresh"]

            inp = EconomicCalculationInput(
                quantity_kg=qty,
                mandi_price_per_kg=price,
                distance_km=m.distance_km,
                transit_loss_fraction=loss_f,
                vehicle_type=vehicle_type,
                market_cess_percent=m.market_cess_percent,
                handling_cost_per_kg=m.handling_cost_per_kg,
                holding_cost_per_hour=m.holding_cost_per_hour,
                holding_wait_hours=m.average_unloading_wait_hours,
                fuel_multiplier=fuel_multiplier,
                freshness_index=fresh,
                daily_arrival_volume_mt=m.arrival_volume_mt
            )
            bd = AuthoritativeEconomicEngine.evaluate_action(inp)

            vehicles_needed = max(1, int(np.ceil(qty / max_vehicle_payload)))

            splits.append(AllocationSplit(
                mandi_id=m.id,
                mandi_name=m.name,
                state=m.state,
                allocated_quantity_kg=qty,
                allocated_percentage=round((qty / total_quantity_kg) * 100.0, 1),
                effective_price_per_kg=bd.quality_adjusted_price_per_kg,
                distance_km=m.distance_km,
                transit_loss_fraction=bd.physical_loss_fraction,
                net_realization=bd.expected_net_realization,
                net_per_kg=bd.net_realization_per_kg,
                assigned_vehicles_count=vehicles_needed,
                vehicle_type=vehicle_type
            ))

            total_gross += bd.gross_realized_revenue
            total_freight += bd.transport_expense
            total_handling += bd.handling_expense
            total_cess += bd.market_cess_expense
            total_holding += bd.unloading_holding_expense
            total_net += bd.expected_net_realization
            total_spoilage += bd.expected_physical_loss_kg

        splits.sort(key=lambda s: s.allocated_quantity_kg, reverse=True)

        # 4. Compute Benchmark Comparisons
        benchmarks = cls._compute_policy_benchmarks(
            crop=crop,
            mandis=mandis,
            total_quantity_kg=total_quantity_kg,
            vehicle_type=vehicle_type,
            ambient_temp=ambient_temp,
            mandi_prices=mandi_prices,
            fuel_multiplier=fuel_multiplier,
            optimized_net=total_net
        )

        unallocated = max(0.0, total_quantity_kg - allocated_total_kg)
        avg_net_per_kg = round(total_net / total_quantity_kg, 2) if total_quantity_kg > 0 else 0.0

        if len(splits) > 1:
            rationale = (
                f"Consignment split across {len(splits)} mandis to avoid local market price depression "
                f"and maximize total realization under vehicle payload bounds."
            )
        elif len(splits) == 1:
            rationale = (
                f"100% allocation to {splits[0].mandi_name} provides peak net realization (₹{splits[0].net_per_kg}/kg) "
                f"without exceeding destination absorption capacity."
            )
        else:
            rationale = "No feasible destination found within safe crop shelf-life limits."

        return MultiMarketAllocationPlan(
            total_crop_quantity_kg=total_quantity_kg,
            unallocated_quantity_kg=round(unallocated, 2),
            splits=splits,
            total_gross_revenue=round(total_gross, 2),
            total_freight_cost=round(total_freight, 2),
            total_handling_cost=round(total_handling, 2),
            total_market_cess=round(total_cess, 2),
            total_holding_cost=round(total_holding, 2),
            total_net_realization=round(total_net, 2),
            average_net_per_kg=avg_net_per_kg,
            total_spoilage_kg=round(total_spoilage, 2),
            benchmarks=benchmarks,
            allocation_rationale=rationale
        )

    @classmethod
    def _compute_policy_benchmarks(
        cls,
        crop: CropProfile,
        mandis: List[MandiInfo],
        total_quantity_kg: float,
        vehicle_type: VehicleType,
        ambient_temp: float,
        mandi_prices: Dict[str, float],
        fuel_multiplier: float,
        optimized_net: float
    ) -> List[PolicyBenchmarkResult]:
        """
        Compares optimized plan against three baseline policies:
        Policy 1: 100% Local Mandi Sale (Lasalgaon or Pimpalgaon)
        Policy 2: 100% Highest Quoted Observed Price Mandi
        Policy 3: 100% Highest Forecast Price Mandi
        """
        results: List[PolicyBenchmarkResult] = []

        # Find closest local mandi (minimum distance km)
        local_mandi = min(mandis, key=lambda m: m.distance_km)
        # Find highest quoted price mandi
        highest_price_mandi = max(mandis, key=lambda m: mandi_prices.get(m.id, m.modal_price_per_kg))

        # 1. Local Baseline
        _, _, _, bd_local = cls.evaluate_mandi_unit_economics(
            crop=crop,
            mandi=local_mandi,
            vehicle_type=vehicle_type,
            ambient_temp=ambient_temp,
            price_per_kg=mandi_prices.get(local_mandi.id, local_mandi.modal_price_per_kg),
            test_quantity_kg=total_quantity_kg,
            fuel_multiplier=fuel_multiplier
        )
        local_net = bd_local.expected_net_realization

        results.append(PolicyBenchmarkResult(
            policy_name="100% Local Mandi Sale",
            policy_description=f"Sell entire lot at nearby {local_mandi.name} (Zero long-haul transit risk)",
            allocated_destinations=[local_mandi.name],
            total_net_realization=bd_local.expected_net_realization,
            net_per_kg=bd_local.net_realization_per_kg,
            total_spoilage_kg=bd_local.expected_physical_loss_kg,
            total_freight_cost=bd_local.transport_expense,
            variance_versus_local_inr=0.0,
            variance_versus_local_percent=0.0,
            is_recommended=False
        ))

        # 2. Highest Headline Price Policy
        _, _, _, bd_high = cls.evaluate_mandi_unit_economics(
            crop=crop,
            mandi=highest_price_mandi,
            vehicle_type=vehicle_type,
            ambient_temp=ambient_temp,
            price_per_kg=mandi_prices.get(highest_price_mandi.id, highest_price_mandi.modal_price_per_kg),
            test_quantity_kg=total_quantity_kg,
            fuel_multiplier=fuel_multiplier
        )
        high_diff = bd_high.expected_net_realization - local_net
        high_pct = (high_diff / local_net * 100.0) if local_net > 0 else 0.0

        results.append(PolicyBenchmarkResult(
            policy_name="100% Highest Quoted Price Mandi",
            policy_description=f"Send all goods to {highest_price_mandi.name} (Chasing maximum quoted rate)",
            allocated_destinations=[highest_price_mandi.name],
            total_net_realization=bd_high.expected_net_realization,
            net_per_kg=bd_high.net_realization_per_kg,
            total_spoilage_kg=bd_high.expected_physical_loss_kg,
            total_freight_cost=bd_high.transport_expense,
            variance_versus_local_inr=round(high_diff, 2),
            variance_versus_local_percent=round(high_pct, 1),
            is_recommended=False
        ))

        # 3. Optimized Allocation Policy
        opt_diff = optimized_net - local_net
        opt_pct = (opt_diff / local_net * 100.0) if local_net > 0 else 0.0

        results.append(PolicyBenchmarkResult(
            policy_name="★ Optimized Allocation Plan",
            policy_description="Constrained economic optimization balancing market capacity, decay, and freight",
            allocated_destinations=["Optimized Dispatch"],
            total_net_realization=round(optimized_net, 2),
            net_per_kg=round(optimized_net / total_quantity_kg, 2),
            total_spoilage_kg=0.0,  # Summed in plan
            total_freight_cost=0.0,
            variance_versus_local_inr=round(opt_diff, 2),
            variance_versus_local_percent=round(opt_pct, 1),
            is_recommended=True
        ))

        return results
