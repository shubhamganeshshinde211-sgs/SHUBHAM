"""
Multi-Mandi Route Optimization Engine.
Evaluates all accessible destination mandis, computes logistics vs decay trade-offs,
and ranks routes by net economic realization.
"""
from typing import List, Dict
from backend.app.models.schemas import (
    OptimizationRequest,
    OptimizationResponse,
    MandiRouteResult,
    RealizationBreakdown,
    VehicleType,
    CropProfile,
    MandiInfo
)
from backend.app.services.decay_engine import TransitDecayEngine
from backend.app.data.mandis_db import get_crop_by_id, get_mandis_for_crop, CROP_CATALOG

class MultiMandiRouteOptimizer:
    """
    Core optimizer that balances market arbitrage against transport freight,
    transit decay, and APMC transaction costs.
    """

    # Freight cost parameters per vehicle type
    VEHICLE_RATES = {
        VehicleType.OPEN_TRUCK: {
            "base_fare": 1200.0,
            "rate_per_km_ton": 3.8,
            "min_km_rate": 28.0,
            "toll_per_km": 1.6
        },
        VehicleType.COVERED_TRUCK: {
            "base_fare": 1600.0,
            "rate_per_km_ton": 4.5,
            "min_km_rate": 34.0,
            "toll_per_km": 1.8
        },
        VehicleType.REEFER_COLD: {
            "base_fare": 4000.0,
            "rate_per_km_ton": 7.8,
            "min_km_rate": 62.0,
            "toll_per_km": 2.2
        }
    }

    @classmethod
    def calculate_freight_cost(
        cls,
        distance_km: float,
        quantity_kg: float,
        vehicle_type: VehicleType,
        fuel_multiplier: float = 1.0
    ) -> float:
        """
        Calculates realistic commercial vehicle freight cost including fuel buffer and tolls.
        """
        v_cost = cls.VEHICLE_RATES.get(vehicle_type, cls.VEHICLE_RATES[VehicleType.COVERED_TRUCK])
        tons = max(0.5, quantity_kg / 1000.0)

        ton_km_cost = distance_km * tons * v_cost["rate_per_km_ton"] * fuel_multiplier
        min_distance_cost = distance_km * v_cost["min_km_rate"] * fuel_multiplier
        transport_freight = v_cost["base_fare"] + max(ton_km_cost, min_distance_cost)
        toll_cost = distance_km * v_cost["toll_per_km"]

        return round(transport_freight + toll_cost, 2)

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

        results: List[MandiRouteResult] = []

        for m in mandis:
            # Check historical database for authentic observed price
            hist_obs = pipeline.storage.get_latest_observation(crop.id, m.id)
            if hist_obs:
                observed_price = float(hist_obs["modal_price_per_kg"])
            else:
                observed_price = m.modal_price_per_kg

            # Obtain evaluated price forecast
            forecast_obj = forecasting_engine.get_forecast(crop.id, m.id, horizon_days=horizon)
            forecasted_price = forecast_obj.predicted_modal_price

            # Active price depending on policy: if forecast_aware, evaluate forecasted price
            effective_price = forecasted_price if request.decision_policy == "forecast_aware" else observed_price

            # 1. Decay calculation
            loss_frac, freshness, decay_expl = TransitDecayEngine.calculate_transit_loss(
                crop=crop,
                mandi=m,
                vehicle_type=request.vehicle_type,
                ambient_temp_celsius=request.ambient_temp_celsius
            )

            # 2. Logistics costs
            transport_cost = cls.calculate_freight_cost(
                distance_km=m.distance_km,
                quantity_kg=request.quantity_kg,
                vehicle_type=request.vehicle_type,
                fuel_multiplier=request.fuel_rate_per_km_multiplier
            )
            handling_cost = round(m.handling_cost_per_kg * request.quantity_kg, 2)
            holding_cost = round(m.holding_cost_per_hour * m.average_unloading_wait_hours, 2)

            # 3. Revenue & APMC Cess
            saleable_kg = round(request.quantity_kg * (1.0 - loss_frac), 2)
            spoilage_kg = round(request.quantity_kg * loss_frac, 2)
            spoilage_val = round(spoilage_kg * effective_price, 2)
            gross_revenue = round(saleable_kg * effective_price, 2)
            market_cess = round(gross_revenue * (m.market_cess_percent / 100.0), 2)

            # 4. Net realization
            total_logistics = round(transport_cost + handling_cost + holding_cost + market_cess, 2)
            net_realization = round(gross_revenue - total_logistics, 2)
            net_per_kg = round(net_realization / request.quantity_kg, 2)
            profit_margin = round((net_realization / gross_revenue * 100.0) if gross_revenue > 0 else 0.0, 1)

            breakdown = RealizationBreakdown(
                gross_revenue=gross_revenue,
                saleable_quantity_kg=saleable_kg,
                spoilage_quantity_kg=spoilage_kg,
                spoilage_value_loss=spoilage_val,
                transport_cost=transport_cost,
                handling_cost=handling_cost,
                market_cess_cost=market_cess,
                holding_cost=holding_cost,
                total_logistics_cost=total_logistics,
                net_realization=net_realization,
                net_per_kg=net_per_kg,
                profit_margin_percent=profit_margin
            )

            # 5. Timing recommendation analysis (Immediate vs Holding H days)
            # Holding cost per kg for H days
            storage_cost_rate = 0.12  # Rs per kg per day
            storage_cost_total = horizon * storage_cost_rate * request.quantity_kg
            # Additional holding biological degradation
            k_storage = crop.hourly_decay_rate * (1.0 if request.vehicle_type == VehicleType.REEFER_COLD else 1.5)
            holding_decay_frac = min(0.35, 1.0 - (2.71828 ** (-k_storage * (horizon * 24.0))))
            total_holding_loss_frac = min(0.85, loss_frac + holding_decay_frac)
            
            future_saleable_kg = request.quantity_kg * (1.0 - total_holding_loss_frac)
            future_gross = future_saleable_kg * forecasted_price
            future_cess = future_gross * (m.market_cess_percent / 100.0)
            future_net = round(future_gross - (transport_cost + handling_cost + holding_cost + storage_cost_total + future_cess), 2)

            net_gain_from_holding = future_net - net_realization
            has_shelf_life = crop.base_shelf_life_hours > (horizon * 24 + m.transit_hours + 12)

            if net_gain_from_holding > (net_realization * 0.08) and has_shelf_life:
                timing_rec = f"Hold & Dispatch on D+{horizon} (Exp. Gain: +₹{net_gain_from_holding:,.0f})"
            elif not has_shelf_life:
                timing_rec = f"Immediate Dispatch (Shelf Life Expiring in {crop.base_shelf_life_hours:.0f}h)"
            else:
                timing_rec = "Immediate Dispatch (Downside/Deterioration Exceeds Price Gain)"

            # 6. Risk classification
            total_duration = m.transit_hours + m.average_unloading_wait_hours
            if loss_frac > 0.15 or (total_duration > 20 and request.vehicle_type != VehicleType.REEFER_COLD):
                risk_level = "High"
            elif loss_frac > 0.06 or m.daily_price_trend == "falling" or forecast_obj.forecast_status.value != "OPTIMAL_MODEL":
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
                net_realization_forecast=future_net
            ))

        # Sort routes by net_realization descending
        results.sort(key=lambda r: r.breakdown.net_realization, reverse=True)

        # Assign ranks and badges
        for idx, r in enumerate(results):
            r.rank = idx + 1
            if idx == 0:
                r.is_recommended = True
                r.recommendation_badge = "★ Best Net Realization"
            elif r.distance_km <= 50:
                r.recommendation_badge = "⚡ Quick Local Dispatch"
            elif r.transit_loss_fraction > 0.12:
                r.recommendation_badge = "⚠ High Spoilage Hazard"
            elif r.freshness_index_percent >= 97.0:
                r.recommendation_badge = "🌱 Max Freshness"

        recommended = results[0]

        # Generate intelligent actionable business insights
        local_route = next((r for r in results if r.distance_km <= 50), None)
        insights = []

        if local_route and recommended.mandi_id != local_route.mandi_id:
            gain = recommended.breakdown.net_realization - local_route.breakdown.net_realization
            insights.append(
                f"Choosing {recommended.mandi_name} over local {local_route.mandi_name} yields an extra "
                f"₹{gain:,.0f} net profit (+₹{recommended.breakdown.net_per_kg - local_route.breakdown.net_per_kg:.2f}/kg), "
                f"as the higher market rate overcomes extra freight."
            )

        if recommended.timing_recommendation:
            insights.append(f"Strategic Dispatch Timing: {recommended.timing_recommendation} for {recommended.mandi_name}.")

        if request.vehicle_type == VehicleType.OPEN_TRUCK and crop.category.value == "high_perishable":
            insights.append(
                f"Warning: Transporting {crop.name} in an open truck at {request.ambient_temp_celsius}°C causes up to "
                f"{recommended.transit_loss_fraction * 100:.1f}% spoilage. Switching to a covered or reefer truck will preserve up to "
                f"₹{recommended.breakdown.spoilage_value_loss * 0.6:,.0f} in crop value."
            )

        long_distance = next((r for r in results if r.distance_km > 700), None)
        if long_distance and long_distance.rank > 2:
            insights.append(
                f"Long-haul terminal {long_distance.mandi_name} offers high nominal price (₹{long_distance.price_per_kg}/kg), "
                f"but {long_distance.transit_loss_fraction * 100:.1f}% transit loss and ₹{long_distance.breakdown.transport_cost:,.0f} freight "
                f"drops its net realization rank to #{long_distance.rank}."
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
            forecast_applied=forecast_applied
        )

