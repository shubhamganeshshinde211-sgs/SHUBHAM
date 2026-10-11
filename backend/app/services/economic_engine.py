"""
Authoritative Single Economic Engine for AgriRoute Intelligence.
Defines mathematically rigorous financial realizations, quality price markdowns,
market absorption limits, and mass conservation invariants.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from backend.app.models.schemas import VehicleType, CropProfile, MandiInfo

@dataclass
class EconomicCalculationInput:
    quantity_kg: float
    mandi_price_per_kg: float
    distance_km: float
    transit_loss_fraction: float
    vehicle_type: VehicleType
    market_cess_percent: float
    handling_cost_per_kg: float
    holding_cost_per_hour: float
    holding_wait_hours: float
    fuel_multiplier: float = 1.0
    storage_days: int = 0
    storage_cost_per_kg_day: float = 0.12
    freshness_index: float = 100.0
    daily_arrival_volume_mt: float = 300.0
    market_absorption_limit_kg: Optional[float] = None
    is_local_baseline: bool = False

@dataclass
class AuthoritativeEconomicBreakdown:
    initial_quantity_kg: float
    expected_quantity_sold_kg: float
    expected_physical_loss_kg: float
    physical_loss_fraction: float
    quoted_market_price_per_kg: float
    quality_adjusted_price_per_kg: float
    quality_discount_per_kg: float
    gross_potential_revenue: float
    gross_realized_revenue: float
    transport_expense: float
    handling_expense: float
    market_cess_expense: float
    unloading_holding_expense: float
    storage_holding_expense: float
    total_logistics_deductions: float
    expected_net_realization: float
    net_realization_per_kg: float
    profit_margin_percent: float
    assumptions_and_warnings: List[str] = field(default_factory=list)

    @property
    def net_realization(self) -> float:
        return self.expected_net_realization


class AuthoritativeEconomicEngine:
    """
    Sole financial authority for AgriRoute Intelligence.
    Ensures:
    1. Mass conservation: Q_initial == Q_sold + Q_lost
    2. Physical loss is deducted strictly from saleable quantity, never double-deducted
    3. Quality deterioration applies a calibrated cosmetic/grade markdown to price
    4. Market absorption discounts prices if shipment volume floods the local mandi
    5. Local baseline is evaluated using identical financial conventions
    """

    # Freight rate structure per vehicle class
    VEHICLE_LOGISTICS = {
        VehicleType.OPEN_TRUCK: {
            "name": "Open Commercial Canter",
            "base_fare": 1200.0,
            "rate_per_km_ton": 3.8,
            "min_km_rate": 28.0,
            "toll_per_km": 1.6,
            "max_payload_kg": 6000.0,
            "fixed_loading_charge": 300.0
        },
        VehicleType.COVERED_TRUCK: {
            "name": "Covered Ventilated Truck",
            "base_fare": 1600.0,
            "rate_per_km_ton": 4.5,
            "min_km_rate": 34.0,
            "toll_per_km": 1.8,
            "max_payload_kg": 9000.0,
            "fixed_loading_charge": 400.0
        },
        VehicleType.REEFER_COLD: {
            "name": "Active Reefer Cold-Chain (+4°C)",
            "base_fare": 4000.0,
            "rate_per_km_ton": 7.8,
            "min_km_rate": 62.0,
            "toll_per_km": 2.2,
            "max_payload_kg": 14000.0,
            "fixed_loading_charge": 750.0
        }
    }

    @classmethod
    def calculate_freight(
        cls,
        distance_km: float,
        quantity_kg: float,
        vehicle_type: VehicleType,
        fuel_multiplier: float = 1.0
    ) -> Tuple[float, List[str]]:
        """
        Calculates commercial freight expense with ton-km, tolls, minimums, and payload limits.
        """
        specs = cls.VEHICLE_LOGISTICS.get(vehicle_type, cls.VEHICLE_LOGISTICS[VehicleType.COVERED_TRUCK])
        warnings = []

        if quantity_kg > specs["max_payload_kg"]:
            warnings.append(
                f"Consignment ({quantity_kg:,.0f} kg) exceeds single {specs['name']} "
                f"payload limit ({specs['max_payload_kg']:,.0f} kg). Multi-vehicle fleet dispatch required."
            )

        payload_tons = max(0.5, quantity_kg / 1000.0)
        ton_km_cost = distance_km * payload_tons * specs["rate_per_km_ton"] * fuel_multiplier
        min_distance_cost = distance_km * specs["min_km_rate"] * fuel_multiplier
        transit_freight = specs["base_fare"] + max(ton_km_cost, min_distance_cost)
        toll_cost = distance_km * specs["toll_per_km"]
        loading_fixed = specs.get("fixed_loading_charge", 0.0)

        total_freight = round(transit_freight + toll_cost + loading_fixed, 2)
        return total_freight, warnings

    @classmethod
    def calculate_quality_markdown(
        cls,
        quoted_price: float,
        freshness_index: float,
        transit_loss_fraction: float
    ) -> Tuple[float, float, List[str]]:
        """
        Computes grade price markdown resulting from quality/freshness deterioration.
        Surviving produce that experiences loss in freshness sells at a slight cosmetic discount.
        Freshness > 92%: 0% discount (Grade A)
        Freshness 80-92%: 2-5% discount (Grade B)
        Freshness < 80%: up to 10-15% discount (Grade C / Distress sale)
        """
        warnings = []
        if freshness_index >= 92.0:
            discount_pct = 0.0
        elif freshness_index >= 80.0:
            # Linear scaling between 0% and 5%
            discount_pct = 0.05 * (1.0 - (freshness_index - 80.0) / 12.0)
            warnings.append(f"Cosmetic grade markdown applied ({discount_pct*100:.1f}%) due to freshness ({freshness_index:.1f}%).")
        else:
            # Deeper markdown between 5% and 15%
            discount_pct = 0.05 + 0.10 * min(1.0, (80.0 - freshness_index) / 30.0)
            warnings.append(f"Significant quality deterioration markdown ({discount_pct*100:.1f}%) due to low freshness ({freshness_index:.1f}%).")

        discount_per_kg = round(quoted_price * discount_pct, 2)
        quality_adjusted_price = max(1.0, round(quoted_price - discount_per_kg, 2))
        return quality_adjusted_price, discount_per_kg, warnings

    @classmethod
    def calculate_market_absorption(
        cls,
        quantity_kg: float,
        daily_arrival_mt: float,
        absorption_limit_kg: Optional[float] = None
    ) -> Tuple[float, List[str]]:
        """
        Evaluates whether consignment volume exerts downward pressure on local mandi prices.
        If shipment > 8% of daily market arrival volume, applies minor price dampening (elasticity factor).
        """
        warnings = []
        market_capacity_kg = absorption_limit_kg or (daily_arrival_mt * 1000.0)
        shipment_share = quantity_kg / max(1000.0, market_capacity_kg)

        if shipment_share > 0.08:
            # Up to 4% local price slippage due to excess supply influx
            slippage_pct = min(0.06, (shipment_share - 0.08) * 0.25)
            warnings.append(
                f"Consignment represents {shipment_share*100:.1f}% of market daily volume. "
                f"Supply pressure may induce {slippage_pct*100:.1f}% price slippage."
            )
            return round(1.0 - slippage_pct, 4), warnings

        return 1.0, warnings

    @classmethod
    def evaluate_action(
        cls,
        inp: EconomicCalculationInput
    ) -> AuthoritativeEconomicBreakdown:
        """
        Executes complete authoritative financial evaluation for a candidate dispatch action.
        """
        warnings: List[str] = []

        # 1. Mass conservation
        loss_fraction = max(0.0, min(0.95, inp.transit_loss_fraction))
        sold_kg = round(inp.quantity_kg * (1.0 - loss_fraction), 2)
        lost_kg = round(inp.quantity_kg - sold_kg, 2)

        # 2. Quality-adjusted pricing
        adj_price, discount_per_kg, q_warns = cls.calculate_quality_markdown(
            quoted_price=inp.mandi_price_per_kg,
            freshness_index=inp.freshness_index,
            transit_loss_fraction=loss_fraction
        )
        warnings.extend(q_warns)

        # 3. Market absorption adjustments
        absorption_multiplier, abs_warns = cls.calculate_market_absorption(
            quantity_kg=inp.quantity_kg,
            daily_arrival_mt=inp.daily_arrival_volume_mt,
            absorption_limit_kg=inp.market_absorption_limit_kg
        )
        warnings.extend(abs_warns)
        final_price_per_kg = round(adj_price * absorption_multiplier, 2)

        # 4. Gross revenues
        # Potential if 100% arrived with 0 loss and 0 quality discount
        gross_potential = round(inp.quantity_kg * inp.mandi_price_per_kg, 2)
        # Actual gross realization from surviving physical produce
        gross_realized = round(sold_kg * final_price_per_kg, 2)

        # 5. Logistics expenditures
        transport_cost, f_warns = cls.calculate_freight(
            distance_km=inp.distance_km,
            quantity_kg=inp.quantity_kg,
            vehicle_type=inp.vehicle_type,
            fuel_multiplier=inp.fuel_multiplier
        )
        warnings.extend(f_warns)

        handling_cost = round(inp.handling_cost_per_kg * inp.quantity_kg, 2)
        unloading_holding_cost = round(inp.holding_cost_per_hour * inp.holding_wait_hours, 2)
        storage_holding_cost = round(inp.storage_days * inp.storage_cost_per_kg_day * inp.quantity_kg, 2)
        market_cess = round(gross_realized * (inp.market_cess_percent / 100.0), 2)

        total_deductions = round(
            transport_cost + handling_cost + unloading_holding_cost + storage_holding_cost + market_cess,
            2
        )

        # 6. Authoritative Net Realization
        net_realization = round(gross_realized - total_deductions, 2)
        net_per_kg = round(net_realization / max(1.0, inp.quantity_kg), 2)
        profit_margin = round((net_realization / gross_realized * 100.0) if gross_realized > 0 else 0.0, 1)

        if net_realization < 0:
            warnings.append(
                f"Negative net realization (₹{net_realization:,.2f}): Total logistics and market deductions exceed gross realized revenue."
            )

        return AuthoritativeEconomicBreakdown(
            initial_quantity_kg=inp.quantity_kg,
            expected_quantity_sold_kg=sold_kg,
            expected_physical_loss_kg=lost_kg,
            physical_loss_fraction=loss_fraction,
            quoted_market_price_per_kg=inp.mandi_price_per_kg,
            quality_adjusted_price_per_kg=final_price_per_kg,
            quality_discount_per_kg=discount_per_kg,
            gross_potential_revenue=gross_potential,
            gross_realized_revenue=gross_realized,
            transport_expense=transport_cost,
            handling_expense=handling_cost,
            market_cess_expense=market_cess,
            unloading_holding_expense=unloading_holding_cost,
            storage_holding_expense=storage_holding_cost,
            total_logistics_deductions=total_deductions,
            expected_net_realization=net_realization,
            net_realization_per_kg=net_per_kg,
            profit_margin_percent=profit_margin,
            assumptions_and_warnings=warnings
        )
