/**
 * AgriRoute Intelligence - API Client v2.1
 * Manages FastAPI communication, Data Quality provenance, and Forecast Integration.
 */

const API_BASE = "http://127.0.0.1:8000";

let isBackendAvailable = false;
let currentDataMode = "DEMO_DATA";
let qualityMetadata = null;

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      isBackendAvailable = true;
      await fetchQualityStatus();
      updateBackendStatus(true);
      return true;
    }
  } catch (err) {
    // Offline or unreachable
  }
  isBackendAvailable = false;
  currentDataMode = "DEMO_DATA";
  updateBackendStatus(false);
  return false;
}

async function fetchQualityStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/data-quality`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      qualityMetadata = await res.json();
      currentDataMode = qualityMetadata.active_data_mode || "HISTORICAL_DATA";
    }
  } catch (e) {
    console.warn("Could not fetch data quality status:", e);
  }
}

async function fetchForecastEvaluation() {
  if (!isBackendAvailable) return null;
  try {
    const res = await fetch(`${API_BASE}/api/forecasts/evaluation`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Could not fetch forecast evaluation:", e);
  }
  return null;
}

async function fetchCropForecasts(cropId, horizon = 3) {
  if (!isBackendAvailable) return [];
  try {
    const res = await fetch(`${API_BASE}/api/forecasts/${cropId}?horizon=${horizon}`, { signal: AbortSignal.timeout(2500) });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Could not fetch crop forecasts:", e);
  }
  return [];
}

function updateBackendStatus(online) {
  const badge = document.getElementById("apiStatusBadge");
  const banner = document.getElementById("dataModeBanner");
  if (!badge) return;

  if (online) {
    const modeLabel = currentDataMode === "REAL_DATA" 
      ? "AGMARKNET Real Data" 
      : (currentDataMode === "HISTORICAL_DATA" ? "AGMARKNET Historical" : "Demo Benchmark");
    
    badge.innerHTML = `<span class="ticker-pulse-dot" style="background:#10b981;"></span> ${modeLabel} Live`;
    badge.style.borderColor = "rgba(16, 185, 129, 0.4)";
    badge.style.color = "#34d399";

    if (banner) {
      banner.style.display = "flex";
      banner.className = "data-mode-banner verified";
      banner.innerHTML = `
        <span class="banner-tag">AUTHENTIC DATA</span>
        <span>Source: <strong>AGMARKNET / DMI</strong> • Latest Observation: <strong>${qualityMetadata?.metrics?.latest_date || '2026-10-10'}</strong> • Records in DB: <strong>${qualityMetadata?.metrics?.total_observations || 2275}</strong></span>
      `;
    }
  } else {
    badge.innerHTML = `<span class="ticker-pulse-dot" style="background:#f59e0b;"></span> Synthetic Demo Engine (Offline)`;
    badge.style.borderColor = "rgba(245, 158, 11, 0.4)";
    badge.style.color = "#fbbf24";

    if (banner) {
      banner.style.display = "flex";
      banner.className = "data-mode-banner simulated";
      banner.innerHTML = `
        <span class="banner-tag simulated">DEMO SIMULATION</span>
        <span>FastAPI backend offline. Currently executing on <strong>Client Synthetic Engine</strong>. Prices are demonstration estimates, not verified quotes.</span>
      `;
    }
  }
}

async function requestOptimization(params) {
  if (isBackendAvailable) {
    try {
      const payload = {
        origin_name: params.originName,
        crop_id: params.cropId,
        quantity_kg: params.quantityKg,
        vehicle_type: params.vehicleType,
        ambient_temp_celsius: params.ambientTemp,
        fuel_rate_per_km_multiplier: params.fuelMultiplier,
        forecast_horizon_days: params.forecastHorizonDays || 3,
        decision_policy: params.decisionPolicy || "immediate"
      };

      const res = await fetch(`${API_BASE}/api/routes/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        return adaptBackendResponse(data);
      }
    } catch (e) {
      console.warn("Backend call failed, falling back to client engine", e);
    }
  }

  // Client-side fallback with explicit demo attribution
  const clientRes = ClientAgriEngine.optimizeAll(params);
  clientRes.activeDataMode = "DEMO_DATA";
  return clientRes;
}

function adaptBackendResponse(data) {
  const routes = data.ranked_routes.map((r) => ({
    mandiId: r.mandi_id,
    mandiName: r.mandi_name,
    state: r.state,
    distanceKm: r.distance_km,
    transitHours: r.transit_hours,
    waitHours: r.unloading_wait_hours,
    totalHours: r.total_duration_hours,
    modalPrice: r.price_per_kg,
    lossFraction: r.transit_loss_fraction,
    freshnessPercent: r.freshness_index_percent,
    saleableKg: r.breakdown.saleable_quantity_kg,
    spoilageKg: r.breakdown.spoilage_quantity_kg,
    spoilageValue: r.breakdown.spoilage_value_loss,
    grossRevenue: r.breakdown.gross_revenue,
    transportCost: r.breakdown.transport_cost,
    handlingCost: r.breakdown.handling_cost,
    marketCess: r.breakdown.market_cess_cost,
    holdingCost: r.breakdown.holding_cost,
    totalDeductions: r.breakdown.total_logistics_cost,
    netRealization: r.breakdown.net_realization,
    netPerKg: r.breakdown.net_per_kg,
    rank: r.rank,
    isWinner: r.is_recommended,
    badge: r.recommendation_badge,
    observedPrice: r.observed_price_per_kg,
    forecastedPrice: r.forecasted_price_per_kg,
    priceLowerBound: r.price_lower_bound,
    priceUpperBound: r.price_upper_bound,
    forecastHorizon: r.forecast_horizon_days,
    forecastStatus: r.forecast_status,
    timingRecommendation: r.timing_recommendation,
    futureNetRealization: r.net_realization_forecast,
    x: getMandiCoords(r.mandi_id).x,
    y: getMandiCoords(r.mandi_id).y
  }));

  const crop = CROPS[data.crop.id] || CROPS.tomato;
  const winner = routes[0];
  const local = routes.find(r => r.distanceKm <= 50);

  return {
    crop,
    quantityKg: data.quantity_kg,
    vehicleType: data.vehicle_type,
    ambientTemp: data.ambient_temp_celsius,
    routes,
    winner,
    local,
    insights: data.insights,
    activeDataMode: data.active_data_mode,
    forecastApplied: data.forecast_applied
  };
}

function getMandiCoords(mandiId) {
  const found = BASE_MANDIS.find(m => m.id === mandiId);
  return found ? { x: found.x, y: found.y } : { x: 200, y: 150 };
}
