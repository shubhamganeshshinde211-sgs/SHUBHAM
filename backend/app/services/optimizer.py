"""
Multi-Mandi Route Optimization & Constrained Dispatch Allocation Engine.
Evaluates all accessible destination mandis, computes logistics vs decay trade-offs,
executes single authoritative economic realizations, evaluates multi-market LP allocation splits,
and ranks routes by risk-adjusted realization under Conservative, Balanced, and Return-Seeking policies.
"""
from typing import List, Dict, Optional
from backend.app.models.schemas import (
    OptimizationRequest,
    OptimizationResponse,
    MandiRouteResult,
    RealizationBreakdown,
    VehicleType,
    CropProfile,
    MandiInfo,
    ScenarioEvaluationSchema,
    MandiRiskProfileSchema,
    AllocationSplitItem,
    PolicyBenchmarkItem,
    MultiMarketAllocationPlanSchema
)
from backend.app.services.decay_engine import TransitDecayEngine
from backend.app.services.economic_engine import (
    AuthoritativeEconomicEngine,
    EconomicCalculationInput
)
from backend.app.services.risk_engine import RiskAwareDecisionEngine, RiskPolicy
from backend.app.services.allocation_optimizer import MultiMarketAllocationOptimizer
from backend.app.data.mandis_db import get_crop_by_id, get_mandis_for_crop, CROP_CATALOG

class MultiMandiRouteOptimizer:
    """
    Core optimizer that balances market arbitrage against transport freight,
    transit decay, APMC transaction costs, and downside forecast volatility.
    """

    @classmethod
    def calculate_freight_cost(
        cls,
        distance_km: float,
        quantity_kg: float,
        vehicle_type: VehicleType,
        fuel_multiplier: float = 1.0
    ) -> float:
        """
        Calculates commercial vehicle freight cost including fuel buffer and tolls
        delegating directly to AuthoritativeEconomicEngine.
        """
        cost, _ = AuthoritativeEconomicEngine.calculate_freight(
            distance_km=distance_km,
            quantity_kg=quantity_kg,
            vehicle_type=vehicle_type,
            fuel_multiplier=fuel_multiplier
        )
        return cost

    @classmethod
    def optimize(cls, request: OptimizationRequest) -> OptimizationResponse:
        from backend.app.data_pipeline.pipeline import MarketDataPipeline
        from backend.app.forecasting.engine import PriceForecastingEngine

        crop: CropProfile = get_crop_by_id(request.crop_id) or CROP_CATALOG["tomato"]
        mandis: List[MandiInfo] = request.custom_mandis or get_mandis_for_crop(request.crop_id)

        pipeline = MarketDataPipeline()
        data_mode = pipeline.get_current_data_mode().value
        forecasting_engine = PriceForecastingEngine(storage=pipeline.storage)

        horizon = request.forecast_horizon_days or 3
        forecast_applied = bool(request.forecast_horizon_days is not None or request.decision_policy == "forecast_aware")

        # Parse selected risk policy
        try:
            risk_policy = RiskPolicy(request.risk_policy.lower()) if request.risk_policy else RiskPolicy.BALANCED
        except Exception:
            risk_policy = RiskPolicy.BALANCED

        # 1. Compute Local Mandi Baseline for comparative reference (closest local node)
        local_mandi = min(mandis, key=lambda m: m.distance_km)
        local_obs = pipeline.storage.get_latest_observation(crop.id, local_mandi.id)
        local_price = float(local_obs["modal_price_per_kg"]) if local_obs else local_mandi.modal_price_per_kg

        local_loss, local_fresh, _ = TransitDecayEngine.calculate_transit_loss(
            crop=crop,
            mandi=local_mandi,
            vehicle_type=request.vehicle_type,
            ambient_temp_celsius=request.ambient_temp_celsius
        )
        local_inp = EconomicCalculationInput(
            quantity_kg=request.quantity_kg,
            mandi_price_per_kg=local_price,
            distance_km=local_mandi.distance_km,
            transit_loss_fraction=local_loss,
            vehicle_type=request.vehicle_type,
            market_cess_percent=local_mandi.market_cess_percent,
            handling_cost_per_kg=local_mandi.handling_cost_per_kg,
            holding_cost_per_hour=local_mandi.holding_cost_per_hour,
            holding_wait_hours=local_mandi.average_unloading_wait_hours,
            fuel_multiplier=request.fuel_rate_per_km_multiplier,
            freshness_index=local_fresh,
            daily_arrival_volume_mt=local_mandi.arrival_volume_mt,
            is_local_baseline=True
        )
        local_breakdown = AuthoritativeEconomicEngine.evaluate_action(local_inp)
        local_expected_net = local_breakdown.expected_net_realization

        # 2. Evaluate Candidate Mandis with Authoritative Engine & Risk Profiles
        results: List[MandiRouteResult] = []
        effective_price_map: Dict[str, float] = {}

        for m in mandis:
            hist_obs = pipeline.storage.get_latest_observation(crop.id, m.id)
            observed_price = float(hist_obs["modal_price_per_kg"]) if hist_obs else m.modal_price_per_kg

            forecast_obj = forecasting_engine.get_forecast(crop.id, m.id, horizon_days=horizon)
            forecasted_price = forecast_obj.predicted_modal_price

            effective_price = forecasted_price if request.decision_policy == "forecast_aware" else observed_price
            effective_price_map[m.id] = effective_price

            # Transit decay kinetics
            loss_frac, freshness, decay_expl = TransitDecayEngine.calculate_transit_loss(
                crop=crop,
                mandi=m,
                vehicle_type=request.vehicle_type,
                ambient_temp_celsius=request.ambient_temp_celsius
            )

            # Authoritative economic calculation
            inp = EconomicCalculationInput(
                quantity_kg=request.quantity_kg,
                mandi_price_per_kg=effective_price,
                distance_km=m.distance_km,
                transit_loss_fraction=loss_frac,
                vehicle_type=request.vehicle_type,
                market_cess_percent=m.market_cess_percent,
                handling_cost_per_kg=m.handling_cost_per_kg,
                holding_cost_per_hour=m.holding_cost_per_hour,
                holding_wait_hours=m.average_unloading_wait_hours,
                fuel_multiplier=request.fuel_rate_per_km_multiplier,
                freshness_index=freshness,
                daily_arrival_volume_mt=m.arrival_volume_mt
            )
            auth_bd = AuthoritativeEconomicEngine.evaluate_action(inp)

            # Map to standard RealizationBreakdown schema
            breakdown = RealizationBreakdown(
                gross_revenue=auth_bd.gross_realized_revenue,
                saleable_quantity_kg=auth_bd.expected_quantity_sold_kg,
                spoilage_quantity_kg=auth_bd.expected_physical_loss_kg,
                spoilage_value_loss=round(auth_bd.expected_physical_loss_kg * effective_price, 2),
                transport_cost=auth_bd.transport_expense,
                handling_cost=auth_bd.handling_expense,
                market_cess_cost=auth_bd.market_cess_expense,
                holding_cost=auth_bd.unloading_holding_expense,
                total_logistics_cost=auth_bd.total_logistics_deductions,
                net_realization=auth_bd.expected_net_realization,
                net_per_kg=auth_bd.net_realization_per_kg,
                profit_margin_percent=auth_bd.profit_margin_percent
            )

            # Timing analysis (Immediate vs Holding H days)
            storage_cost_rate = 0.12
            storage_cost_total = horizon * storage_cost_rate * request.quantity_kg
            k_storage = crop.hourly_decay_rate * (1.0 if request.vehicle_type == VehicleType.REEFER_COLD else 1.5)
            holding_decay_frac = min(0.35, 1.0 - (2.71828 ** (-k_storage * (horizon * 24.0))))
            total_holding_loss_frac = min(0.85, loss_frac + holding_decay_frac)
            
            future_saleable_kg = request.quantity_kg * (1.0 - total_holding_loss_frac)
            future_gross = future_saleable_kg * forecasted_price
            future_cess = future_gross * (m.market_cess_percent / 100.0)
            future_net = round(
                future_gross - (auth_bd.transport_expense + auth_bd.handling_expense + auth_bd.unloading_holding_expense + storage_cost_total + future_cess),
                2
            )
            net_gain_from_holding = future_net - auth_bd.expected_net_realization
            has_shelf_life = crop.base_shelf_life_hours > (horizon * 24 + m.transit_hours + 12)

            if net_gain_from_holding > (auth_bd.expected_net_realization * 0.08) and has_shelf_life:
                timing_rec = f"Hold & Dispatch on D+{horizon} (Exp. Gain: +₹{net_gain_from_holding:,.0f})"
            elif not has_shelf_life:
                timing_rec = f"Immediate Dispatch (Shelf Life Expiring in {crop.base_shelf_life_hours:.0f}h)"
            else:
                timing_rec = "Immediate Dispatch (Downside/Deterioration Exceeds Price Gain)"

            # Risk and Scenario stress testing
            risk_profile = RiskAwareDecisionEngine.evaluate_mandi_scenarios(
                crop=crop,
                mandi=m,
                quantity_kg=request.quantity_kg,
                base_price=effective_price,
                vehicle_type=request.vehicle_type,
                ambient_temp=request.ambient_temp_celsius,
                fuel_multiplier=request.fuel_rate_per_km_multiplier,
                price_lower_bound=forecast_obj.lower_bound_price,
                price_upper_bound=forecast_obj.upper_bound_price,
                risk_policy=risk_policy,
                local_expected_net=local_expected_net
            )

            # Scenario schema mapping
            scenario_schemas = [
                ScenarioEvaluationSchema(
                    scenario_id=s.scenario_id,
                    scenario_name=s.scenario_name,
                    description=s.description,
                    price_factor=s.price_factor,
                    freight_factor=s.freight_factor,
                    decay_factor=s.decay_factor,
                    effective_price_per_kg=s.effective_price_per_kg,
                    transit_loss_fraction=s.transit_loss_fraction,
                    net_realization=s.net_realization,
                    net_per_kg=s.net_per_kg,
                    profit_margin_percent=s.profit_margin_percent,
                    variance_versus_expected_inr=s.variance_versus_expected_inr,
                    is_downside=s.is_downside
                )
                for s in risk_profile.scenarios
            ]

            total_duration = m.transit_hours + m.average_unloading_wait_hours
            if loss_frac > 0.15 or (total_duration > 20 and request.vehicle_type != VehicleType.REEFER_COLD):
                risk_level = "High"
            elif loss_frac > 0.06 or not risk_profile.is_resilient:
                risk_level = "Moderate"
            else:
                risk_level = "Low"

            results.append(MandiRouteResult(
                mandi_id=m.id,
                mandi_name=m.name,
                state=m.state,
                distance_km=m.distance_km,
                transit_hours=m.transit_hours,
                unloading_wait_hours=m.average_unloading_wait_hours,
                total_duration_hours=total_duration,
                vehicle_type=request.vehicle_type,
                transit_loss_fraction=loss_frac,
                decay_explanation=decay_expl,
                price_per_kg=effective_price,
                breakdown=breakdown,
                freshness_index_percent=freshness,
                is_recommended=False,
                rank=1,
                recommendation_badge="",
                risk_level=risk_level,
                observed_price_per_kg=observed_price,
                forecasted_price_per_kg=forecasted_price,
                price_lower_bound=forecast_obj.lower_bound_price,
                price_upper_bound=forecast_obj.upper_bound_price,
                forecast_horizon_days=horizon,
                forecast_status=forecast_obj.forecast_status.value,
                data_mode=data_mode,
                timing_recommendation=timing_rec,
                net_realization_forecast=future_net,
                risk_adjusted_score=risk_profile.risk_adjusted_score,
                downside_var_90_inr=risk_profile.downside_var_90_inr,
                is_resilient=risk_profile.is_resilient,
                scenarios=scenario_schemas,
                risk_policy_explanation=risk_profile.policy_explanation
            ))

        # 3. Policy-Based Sorting
        # Under Conservative/Balanced policies, rank by risk_adjusted_score;
        # under Return-Seeking, rank purely by net_realization.
        if risk_policy == RiskPolicy.RETURN_SEEKING:
            results.sort(key=lambda r: r.breakdown.net_realization, reverse=True)
        else:
            results.sort(key=lambda r: (r.risk_adjusted_score or r.breakdown.net_realization), reverse=True)

        for idx, r in enumerate(results):
            r.rank = idx + 1
            if idx == 0:
                r.is_recommended = True
                r.recommendation_badge = "★ Best Risk-Adjusted Net" if risk_policy != RiskPolicy.RETURN_SEEKING else "★ Best Net Realization"
            elif r.distance_km <= 50:
                r.recommendation_badge = "⚡ Quick Local Dispatch"
            elif r.transit_loss_fraction > 0.12:
                r.recommendation_badge = "⚠ High Spoilage Hazard"
            elif r.freshness_index_percent >= 97.0:
                r.recommendation_badge = "🌱 Max Freshness"

        recommended = results[0]

        # 4. Solve Multi-Market Allocation Plan
        allow_split = request.allow_multi_market_split if request.allow_multi_market_split is not None else True
        allocation_plan_obj = MultiMarketAllocationOptimizer.solve_allocation(
            crop=crop,
            mandis=mandis,
            total_quantity_kg=request.quantity_kg,
            vehicle_type=request.vehicle_type,
            ambient_temp=request.ambient_temp_celsius,
            mandi_prices=effective_price_map,
            fuel_multiplier=request.fuel_rate_per_km_multiplier,
            allow_splitting=allow_split
        )

        # Convert allocation plan to Pydantic schema
        splits_schemas = [
            AllocationSplitItem(
                mandi_id=s.mandi_id,
                mandi_name=s.mandi_name,
                state=s.state,
                allocated_quantity_kg=s.allocated_quantity_kg,
                allocated_percentage=s.allocated_percentage,
                effective_price_per_kg=s.effective_price_per_kg,
                distance_km=s.distance_km,
                transit_loss_fraction=s.transit_loss_fraction,
                net_realization=s.net_realization,
                net_per_kg=s.net_per_kg,
                assigned_vehicles_count=s.assigned_vehicles_count,
                vehicle_type=s.vehicle_type
            )
            for s in allocation_plan_obj.splits
        ]

        benchmarks_schemas = [
            PolicyBenchmarkItem(
                policy_name=b.policy_name,
                policy_description=b.policy_description,
                allocated_destinations=b.allocated_destinations,
                total_net_realization=b.total_net_realization,
                net_per_kg=b.net_per_kg,
                total_spoilage_kg=b.total_spoilage_kg,
                total_freight_cost=b.total_freight_cost,
                variance_versus_local_inr=b.variance_versus_local_inr,
                variance_versus_local_percent=b.variance_versus_local_percent,
                is_recommended=b.is_recommended
            )
            for b in allocation_plan_obj.benchmarks
        ]

        allocation_schema = MultiMarketAllocationPlanSchema(
            total_crop_quantity_kg=allocation_plan_obj.total_crop_quantity_kg,
            unallocated_quantity_kg=allocation_plan_obj.unallocated_quantity_kg,
            splits=splits_schemas,
            total_gross_revenue=allocation_plan_obj.total_gross_revenue,
            total_freight_cost=allocation_plan_obj.total_freight_cost,
            total_handling_cost=allocation_plan_obj.total_handling_cost,
            total_market_cess=allocation_plan_obj.total_market_cess,
            total_holding_cost=allocation_plan_obj.total_holding_cost,
            total_net_realization=allocation_plan_obj.total_net_realization,
            average_net_per_kg=allocation_plan_obj.average_net_per_kg,
            total_spoilage_kg=allocation_plan_obj.total_spoilage_kg,
            benchmarks=benchmarks_schemas,
            allocation_rationale=allocation_plan_obj.allocation_rationale
        )

        # 5. Business & Risk Insights
        insights: List[str] = []

        local_route = next((r for r in results if r.distance_km <= 50), None)
        if local_route and recommended.mandi_id != local_route.mandi_id:
            gain = recommended.breakdown.net_realization - local_route.breakdown.net_realization
            insights.append(
                f"Choosing {recommended.mandi_name} over local {local_route.mandi_name} yields an extra "
                f"₹{gain:,.0f} net profit (+₹{recommended.breakdown.net_per_kg - local_route.breakdown.net_per_kg:.2f}/kg), "
                f"as the higher market rate overcomes extra freight."
            )

        insights.append(
            f"Risk Policy [{risk_policy.value.upper()}]: Evaluated {len(recommended.scenarios or [])} market stress scenarios. "
            f"Maximum Downside VaR-90 is ₹{recommended.downside_var_90_inr:,.0f} ({recommended.risk_level} risk)."
        )

        if recommended.timing_recommendation:
            insights.append(f"Strategic Dispatch Timing: {recommended.timing_recommendation} for {recommended.mandi_name}.")

        if len(allocation_schema.splits) > 1:
            split_summary = ", ".join(f"{s.mandi_name} ({s.allocated_percentage}%)" for s in allocation_schema.splits)
            insights.append(f"Multi-Market Optimization: Splitting consignment across {split_summary} prevents local price depression.")

        if request.vehicle_type == VehicleType.OPEN_TRUCK and crop.category.value == "high_perishable":
            insights.append(
                f"Warning: Transporting {crop.name} in an open truck at {request.ambient_temp_celsius}°C causes up to "
                f"{recommended.transit_loss_fraction * 100:.1f}% spoilage. Switching to a covered or reefer truck will preserve up to "
                f"₹{recommended.breakdown.spoilage_value_loss * 0.6:,.0f} in crop value."
            )

        return OptimizationResponse(
            origin_name=request.origin_name,
            crop=crop,
            quantity_kg=request.quantity_kg,
            vehicle_type=request.vehicle_type,
            ambient_temp_celsius=request.ambient_temp_celsius,
            ranked_routes=results,
            recommended_mandi=recommended,
            insights=insights,
            active_data_mode=data_mode,
            forecast_applied=forecast_applied,
            allocation_plan=allocation_schema,
            risk_policy_applied=risk_policy.value,
            local_baseline_net=local_expected_net
        )
