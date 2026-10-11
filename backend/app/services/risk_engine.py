"""
Uncertainty and Risk-Aware Decision Service for AgriRoute Intelligence.
Evaluates scenario sensitivities, downside Value-at-Risk (VaR),
and enforces explicit Risk Policies: Conservative, Balanced, and Return-Seeking.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from backend.app.models.schemas import VehicleType, CropProfile, MandiInfo
from backend.app.services.economic_engine import (
    AuthoritativeEconomicEngine,
    EconomicCalculationInput,
    AuthoritativeEconomicBreakdown
)
from backend.app.services.decay_engine import TransitDecayEngine

class RiskPolicy(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    RETURN_SEEKING = "return_seeking"

@dataclass
class ScenarioEvaluation:
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

@dataclass
class MandiRiskProfile:
    mandi_id: str
    mandi_name: str
    expected_net_realization: float
    risk_adjusted_score: float
    risk_policy: RiskPolicy
    scenarios: List[ScenarioEvaluation]
    downside_var_90_inr: float          # Value-at-Risk (downside tail loss)
    max_drawdown_versus_local_inr: float # Maximum loss vs safe local option in severe stress
    downside_risk_ratio: float           # Relative downside volatility
    is_resilient: bool
    policy_explanation: str

class RiskAwareDecisionEngine:
    """
    Evaluates market decisions under deep forecast and operational uncertainty.
    """

    POLICY_WEIGHTS = {
        RiskPolicy.CONSERVATIVE: {"downside_penalty": 0.70, "min_margin_threshold": 12.0},
        RiskPolicy.BALANCED: {"downside_penalty": 0.30, "min_margin_threshold": 5.0},
        RiskPolicy.RETURN_SEEKING: {"downside_penalty": 0.00, "min_margin_threshold": 0.0}
    }

    @classmethod
    def evaluate_mandi_scenarios(
        cls,
        crop: CropProfile,
        mandi: MandiInfo,
        quantity_kg: float,
        base_price: float,
        vehicle_type: VehicleType,
        ambient_temp: float,
        fuel_multiplier: float = 1.0,
        price_lower_bound: Optional[float] = None,
        price_upper_bound: Optional[float] = None,
        risk_policy: RiskPolicy = RiskPolicy.BALANCED,
        local_expected_net: float = 0.0
    ) -> MandiRiskProfile:
        """
        Runs 5 canonical stress-test scenarios for a mandi route:
        1. Expected Base Case
        2. Bear Market Drop (-15% or lower confidence bound)
        3. Bull Market Surge (+15% or upper confidence bound)
        4. Freight & Toll Spike (+25% transport cost)
        5. Severe Transit Delay / Heatwave (+50% spoilage acceleration)
        """
        # Baseline decay
        base_loss_frac, freshness, _ = TransitDecayEngine.calculate_transit_loss(
            crop=crop,
            mandi=mandi,
            vehicle_type=vehicle_type,
            ambient_temp_celsius=ambient_temp
        )

        scenarios_defs = [
            {
                "id": "expected",
                "name": "Expected Base Case",
                "desc": "Baseline price and standard highway travel conditions",
                "price": base_price,
                "freight_mult": fuel_multiplier,
                "loss_frac": base_loss_frac,
                "price_factor": 1.0,
                "freight_factor": 1.0,
                "decay_factor": 1.0,
                "is_downside": False
            },
            {
                "id": "bear_market",
                "name": "Bear Market Influx (-15%)",
                "desc": "Heavy mandi arrivals depress clearing prices",
                "price": price_lower_bound if price_lower_bound else round(base_price * 0.85, 2),
                "freight_mult": fuel_multiplier,
                "loss_frac": base_loss_frac,
                "price_factor": (price_lower_bound / base_price) if price_lower_bound else 0.85,
                "freight_factor": 1.0,
                "decay_factor": 1.0,
                "is_downside": True
            },
            {
                "id": "bull_market",
                "name": "Bull Market Deficit (+15%)",
                "desc": "Terminal demand surge expands market arbitrage",
                "price": price_upper_bound if price_upper_bound else round(base_price * 1.15, 2),
                "freight_mult": fuel_multiplier,
                "loss_frac": base_loss_frac,
                "price_factor": (price_upper_bound / base_price) if price_upper_bound else 1.15,
                "freight_factor": 1.0,
                "decay_factor": 1.0,
                "is_downside": False
            },
            {
                "id": "high_freight",
                "name": "Diesel & Toll Spike (+25%)",
                "desc": "Fuel surcharge escalation and highway bottleneck charges",
                "price": base_price,
                "freight_mult": fuel_multiplier * 1.25,
                "loss_frac": base_loss_frac,
                "price_factor": 1.0,
                "freight_factor": 1.25,
                "decay_factor": 1.0,
                "is_downside": True
            },
            {
                "id": "severe_spoilage",
                "name": "Extreme Heat & Delay (+50% decay)",
                "desc": "Severe ambient heat wave and terminal gate waiting congestion",
                "price": base_price,
                "freight_mult": fuel_multiplier,
                "loss_frac": min(0.92, base_loss_frac * 1.50),
                "price_factor": 1.0,
                "freight_factor": 1.0,
                "decay_factor": 1.50,
                "is_downside": True
            }
        ]

        evaluated_scenarios: List[ScenarioEvaluation] = []
        expected_net = 0.0

        for sc in scenarios_defs:
            inp = EconomicCalculationInput(
                quantity_kg=quantity_kg,
                mandi_price_per_kg=sc["price"],
                distance_km=mandi.distance_km,
                transit_loss_fraction=sc["loss_frac"],
                vehicle_type=vehicle_type,
                market_cess_percent=mandi.market_cess_percent,
                handling_cost_per_kg=mandi.handling_cost_per_kg,
                holding_cost_per_hour=mandi.holding_cost_per_hour,
                holding_wait_hours=mandi.average_unloading_wait_hours,
                fuel_multiplier=sc["freight_mult"],
                freshness_index=freshness,
                daily_arrival_volume_mt=mandi.arrival_volume_mt
            )
            bd = AuthoritativeEconomicEngine.evaluate_action(inp)

            if sc["id"] == "expected":
                expected_net = bd.expected_net_realization

            diff_from_expected = bd.expected_net_realization - expected_net

            evaluated_scenarios.append(ScenarioEvaluation(
                scenario_id=sc["id"],
                scenario_name=sc["name"],
                description=sc["desc"],
                price_factor=sc["price_factor"],
                freight_factor=sc["freight_factor"],
                decay_factor=sc["decay_factor"],
                effective_price_per_kg=bd.quality_adjusted_price_per_kg,
                transit_loss_fraction=bd.physical_loss_fraction,
                net_realization=bd.expected_net_realization,
                net_per_kg=bd.net_realization_per_kg,
                profit_margin_percent=bd.profit_margin_percent,
                variance_versus_expected_inr=round(diff_from_expected, 2),
                is_downside=sc["is_downside"]
            ))

        # Re-update variances for non-expected relative to expected
        for s in evaluated_scenarios:
            s.variance_versus_expected_inr = round(s.net_realization - expected_net, 2)

        # Risk calculations
        downside_losses = [abs(s.variance_versus_expected_inr) for s in evaluated_scenarios if s.is_downside and s.variance_versus_expected_inr < 0]
        max_downside_loss = max(downside_losses) if downside_losses else 0.0
        worst_scenario_net = min(s.net_realization for s in evaluated_scenarios)
        max_drawdown_vs_local = round(local_expected_net - worst_scenario_net, 2) if local_expected_net > 0 else 0.0

        p_weights = cls.POLICY_WEIGHTS.get(risk_policy, cls.POLICY_WEIGHTS[RiskPolicy.BALANCED])
        penalty = p_weights["downside_penalty"]

        # Risk-adjusted score = ExpectedNet - lambda * MaxDownsideLoss
        risk_adjusted_score = round(expected_net - (penalty * max_downside_loss), 2)
        downside_risk_ratio = round((max_downside_loss / expected_net), 3) if expected_net > 0 else 1.0

        # Resilience criteria:
        # A route is resilient if under the worst-case scenario its profit margin > 0 and drawdown vs local < 10%
        is_resilient = (worst_scenario_net > 0) and (max_drawdown_vs_local <= (expected_net * 0.12))

        if risk_policy == RiskPolicy.CONSERVATIVE:
            explanation = (
                f"Conservative policy penalizes downside volatility by {penalty*100:.0f}%. "
                f"Route score discounted by ₹{penalty * max_downside_loss:,.0f} due to potential bear-market or spoilage risks."
            )
        elif risk_policy == RiskPolicy.RETURN_SEEKING:
            explanation = (
                f"Return-seeking policy accepts downside variance to target maximum headline profit (₹{expected_net:,.0f})."
            )
        else:
            explanation = (
                f"Balanced policy applies a moderate {penalty*100:.0f}% buffer against adverse price shifts and highway delays."
            )

        return MandiRiskProfile(
            mandi_id=mandi.id,
            mandi_name=mandi.name,
            expected_net_realization=round(expected_net, 2),
            risk_adjusted_score=risk_adjusted_score,
            risk_policy=risk_policy,
            scenarios=evaluated_scenarios,
            downside_var_90_inr=round(max_downside_loss, 2),
            max_drawdown_versus_local_inr=max_drawdown_vs_local,
            downside_risk_ratio=downside_risk_ratio,
            is_resilient=is_resilient,
            policy_explanation=explanation
        )
