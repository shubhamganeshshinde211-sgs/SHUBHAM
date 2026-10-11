# AGRIROUTE INTELLIGENCE — PHASE 5 AUDIT & VERIFICATION REPORT

**Date:** 2026-10-11  
**Auditor:** Antigravity AI  
**Scope:** Architecture, mathematical rigor, data pipeline, forecasting models, economic optimizer, and frontend-backend parity.

---

## 1. Executive Summary

A comprehensive, line-by-line inspection of the AgriRoute Intelligence codebase was conducted across backend services, forecasting modules, database records, mathematical formulations, and frontend client logic.

| Dimension | Verification Status | Key Findings |
| :--- | :---: | :--- |
| **Market Data Authenticity** | **Partially Genuine / Calibrated Benchmark** | 2,275 records stored in SQLite from `AGMARKNET_CSV`. The series is a calibrated historical benchmark grounded in real AGMARKNET price levels for Nashik & terminal mandis. |
| **Source Provenance & Metadata** | **Verified** | Every record retains `source_name`, `retrieved_at` ISO timestamps, `original_price_unit`, `original_modal_price`, and quality validation flags. |
| **Forecast Utilization** | **Verified** | `optimizer.py` queries `PriceForecastingEngine.get_forecast()` and swaps modal price when `decision_policy == "forecast_aware"`, and utilizes forecast prices for holding decisions. |
| **Evaluation Reproducibility** | **Verified** | Evaluation is deterministic (`random_state=42`, strict chronological walk-forward splits in `backtester.py`). 785 out-of-sample observations evaluated. |
| **Cost Units Consistency** | **Verified** | All monetary amounts are strictly denominated in INR (₹). Physical quantities are in kilograms (kg), distances in kilometers (km), durations in hours (h). |
| **Loss & Spoilage Double-Counting** | **Verified (Clean)** | Spoilage reduces saleable physical quantity ($Q_{\text{saleable}} = Q \cdot (1 - L)$); gross revenue is calculated on saleable quantity. Spoilage value is reported for transparency but is **not** subtracted again from revenue. |
| **Route Distances** | **Road Highway Distances (Static)** | Distances reflect actual NH/SH road routes (e.g. 175 km to Vashi, 210 km to Pune, 1,280 km to Delhi), not straight-line haversine approximations. However, route provenance, tolls, and road condition freshness metadata are static. |
| **Holding & Shelf-Life Safety** | **Heuristic** | Holding evaluates $(H \times 24 + \text{transit} + 12) < \text{shelf\_life}$. A conservative rule, but lacks multi-period decay scheduling and quality-tier downgrade modeling. |
| **Frontend vs Backend Parity** | **Divergence Risk** | `engine.js` replicates the decay and freight equations, but derives base prices from a static `priceDelta` heuristic instead of database/forecast states. |
| **Test Mathematical Correctness** | **Incomplete Invariant Coverage** | Existing 21 tests verify schema validity and non-negativity, but lack explicit mathematical monotonicity invariant proofs (freight sensitivity, price monotonicity, mass conservation). |

---

## 2. In-Depth Component Audit

### 2.1 Database & Provenance (`backend/app/data_pipeline/`)
- **Table**: `market_observations` in `backend/data/market_observations.db`.
- **Records**: 2,275 unique rows covering 5 crops (`tomato`, `onion`, `potato`, `green_chilli`, `pomegranate`) across 7 mandis from `2026-07-28` to `2026-10-10`.
- **Schema Fields**:
  - `observation_date` (ISO text), `market_id`, `commodity_id`, `variety`.
  - `modal_price_per_kg`, `min_price_per_kg`, `max_price_per_kg`, `arrivals_mt`.
  - `original_price_unit`, `original_modal_price`, `source_name`, `retrieved_at`, `data_quality_status`.
- **Provenance Quality**: High. Deduplication constraint `uq_mandi_obs` prevents redundant entries. Quality checker flags spikes ($>3.0\times$ median) and negative values.

### 2.2 Forecasting & Backtesting (`backend/app/forecasting/`)
- **Models**: LightGBM Regressor alongside 3 baselines:
  1. `LastObservedBaseline` (Naive persistence)
  2. `RollingAverageBaseline` (7-day window)
  3. `SeasonalNaiveBaseline` (7-day seasonal cycle)
- **Features**: 3d/7d/14d rolling means, rolling standard deviation, momentum ratios, volatility indices, day-of-week, arrivals volume.
- **Evaluation**: Chronological rolling-origin evaluation over 785 out-of-sample samples. Zero future leakage.
- **Artifacts**: 10 `.joblib` models saved in `backend/app/forecasting/models/`.

### 2.3 Economic Optimizer (`backend/app/services/optimizer.py`)
- **Formula**:
  $$\text{Net Realization} = Q \cdot (1 - L) \cdot P - (C_{\text{transport}} + C_{\text{handling}} + C_{\text{holding}} + C_{\text{cess}})$$
- **Transit Spoilage**:
  $$L = \min\left(0.92, 1 - e^{-k_{\text{eff}} \cdot t} + L_{\text{moisture}}\right)$$
  $$k_{\text{eff}} = k_{\text{base}} \cdot 2.1^{\frac{\Delta T}{10}} \cdot V_{\text{vehicle}} \cdot R_{\text{road}}$$
- **Missing Capabilities Identified**:
  1. Single-destination ranking only: Cannot split shipment across multiple mandis ($Q = \sum q_m$).
  2. No vehicle capacity constraint: If user requests 25,000 kg, single vehicle payload limitations are not enforced.
  3. Quality deterioration markdown: No differentiation between physical waste and cosmetic downgrade (e.g. price reduction from B-grade quality).
  4. Market absorption / arrival capacity: Does not penalize dumping 50 tons into a small local mandi.
  5. Downside risk policy: Risk levels are qualitative strings (`"Low"`, `"Moderate"`, `"High"`) rather than mathematically quantified policies (`Conservative`, `Balanced`, `Return-Seeking`).

### 2.4 Frontend vs Backend Dual Engine Audit
- `frontend/js/engine.js`: Replicates freight and decay physics. If API is offline, client computes estimates using `crop.baseBenchmarkPrice + mandi.priceDelta`.
- `frontend/js/api.js`: Prefers FastAPI `POST /api/routes/optimize`.
- **Finding**: While useful for 0ms slider previews, the backend must be the sole authority for dispatch decisions, allocation optimization, and timing recommendations.

---

## 3. Remediation Roadmap for Phase 5

1. **Phase 1 (Single Authoritative Economic Engine)**:
   - Introduce quality-tier price degradation: $P_{\text{eff}} = P \cdot (1 - \delta_{\text{quality}})$.
   - Add market absorption capacity constraints.
   - Implement rigorous mathematical invariant unit tests (freight sensitivity, spoilage monotonicity, mass conservation, local baseline parity).
2. **Phase 2 (Realistic Logistics & Vehicle Fleet)**:
   - Vehicle fleet constraints: Max payload per vehicle (e.g. 1.5t pickup, 5t canter, 16t multi-axle), payload overage rejection.
   - Road route provenance and toll auditing.
3. **Phase 3 (Multi-Market Allocation Optimization)**:
   - Implement constrained mathematical allocation (LP solver via SciPy/PuLP) allowing produce splitting across mandis when profitable or capacity-limited.
   - Benchmark against baseline heuristics: (a) 100% Local Sale, (b) 100% Highest Observed Price, (c) 100% Highest Forecast Price.
4. **Phase 4 (Risk-Aware Decision Making)**:
   - Scenario engine: Expected price, Bear market (-15%), Bull market (+15%), High-freight (+25%), High-decay (+50%).
   - Explicit risk policies: **Conservative** (penalizes volatility and downside tail), **Balanced**, and **Return-Seeking**.
   - Downside Value-at-Risk (VaR) / Conditional Net Realization metrics.
5. **Phase 5 (Frontend Integration & Automated Verification)**:
   - Update UI to display allocation splits, risk policy controls, scenario analysis, and explainable financial breakdown.
   - Expand pytest test suite to ensure comprehensive coverage.
