# Current State Audit: AgriRoute Intelligence

**Date:** 2026-10-11  
**Auditor:** DeepMind Antigravity Pair Programmer  
**Repository:** `C:\Users\VEDANT\.gemini\antigravity-ide\scratch\agriroute-intelligence`

---

## 1. Modules Actually Implemented

### Backend (`backend/app/`)
- **`main.py`**:
  - FastAPI 2.0 app configuration with permissive `CORSMiddleware`.
  - Health check endpoint `GET /health`.
  - Routers included: `optimizer_router`, `market_router`, `realization_router`.
  - Static mount for `frontend/` directory (serving `index.html` at `/`).
- **`models/schemas.py`**:
  - `VehicleType` Enum (`open_truck`, `covered_truck`, `reefer_cold`).
  - `CropCategory` Enum (`high_perishable`, `semi_perishable`, `durable_grain`).
  - `CropProfile`, `MandiInfo`, `RealizationInput`, `RealizationBreakdown`.
  - `OptimizationRequest`, `MandiRouteResult`, `OptimizationResponse`.
- **`services/decay_engine.py`**:
  - `TransitDecayEngine.calculate_transit_loss()` implementing:
    - Temperature delta and $Q_{10}$ thermal acceleration ($2.1^{\Delta T / 10}$).
    - Vehicle decay multipliers (`open_truck`: 1.45x, `covered_truck`: 1.0x, `reefer_cold`: 0.20x).
    - Road condition vibration shock factor ($R \ge 0.8$).
    - Moisture transpiration loss.
    - First-order exponential decay formula $L = 1 - e^{-k_{\text{eff}} \cdot t}$.
- **`services/optimizer.py`**:
  - `MultiMandiRouteOptimizer.calculate_freight_cost()` calculating ton-km freight, base fare, minimum km rate, and highway tolls.
  - Multi-mandi candidate evaluation iterating over mandis, computing decay, logistics, APMC cess, handling, yard holding fees, gross revenue, and net realization.
  - Sorting descending by `net_realization`, assigning ranks, badges, risk levels (`Low`, `Moderate`, `High`), and generating textual business insights.
- **`data/mandis_db.py`**:
  - Static catalog of 8 crops: Tomato, Onion, Potato, Green Chilli, Pomegranate, Banana, Wheat, Soyabean.
  - Baseline network of 7 mandis: Vashi (Mumbai), Pune (Gultekdi), Surat, Lasalgaon, Pimpalgaon Baswant, Azadpur (Delhi), Bowenpally (Hyderabad).
  - Price scaling function `get_mandis_for_crop()` using fixed multipliers and random variance.
- **`routers/optimizer_router.py`**:
  - `POST /api/routes/optimize`: Evaluates route optimization.
  - `GET /api/routes/crops`: Returns list of crop profiles.
  - `GET /api/routes/crops/{crop_id}`: Single crop profile.
- **`routers/market_router.py`**:
  - `GET /api/market-prices/mandis`: Static mandi list for crop.
  - `GET /api/market-prices/live`: Injects random noise into prices and arrivals.
  - `GET /api/market-prices/history/{crop_id}`: Synthesizes a 7-day random walk backward.
- **`routers/realization_router.py`**:
  - `POST /realization`: Backward-compatible single-route unit realization calculation.

### Frontend (`frontend/`)
- **`index.html`**:
  - Dark-slate layout with SEO meta tags, Google Fonts, brand emblem.
  - Real-time ticker marquee (`#tickerMarquee`).
  - Consignment controls: Dispatch cluster selector, crop grid pills, weight slider, vehicle fleet selector, ambient temp slider, fuel surcharge slider.
  - KPI summary cards (Top Mandi, Net Realization, Arbitrage Advantage, Freshness Retained).
  - Canvas 2D Transit Corridor route visualizer (`#corridorCanvas`).
  - Financial realization waterfall chart.
  - Multi-Mandi Leaderboard table (`#leaderboardBody`).
  - AI Strategic Intelligence advice box (`#insightsList`).
  - Consignment Dispatch & Realization Bill modal dialog (`#auditModal`).
- **`css/styles.css`**:
  - Vanilla CSS design tokens (`--bg-base`, `--emerald-500`, `--amber-500`, `--cyan-500`).
  - Glassmorphic card styling, responsive 2-column layout, custom range slider thumbs.
- **`js/engine.js`**:
  - Complete client-side calculation engine implementing biological decay kinetics, road vibration, freight calculation, and multi-mandi ranking.
- **`js/api.js`**:
  - Connects to `http://localhost:8000`.
  - Checks `/health` endpoint; gracefully switches between FastAPI live backend and client neural engine.
  - Adapter function `adaptBackendResponse()` mapping backend response fields to UI state.
- **`js/app.js`**:
  - Event listeners for inputs and sliders.
  - Real-time 60fps HTML5 Canvas rendering of routes and animated vehicle dots.
  - Live ticker interval generator.
  - Modal opener and print handler.

### Server (`serve.ps1`)
- Custom PowerShell HTTP server based on `System.Net.HttpListener`.
- Serves `frontend/` on port 8080 with CORS headers and MIME type mapping. Currently running in background as a daemon task.

---

## 2. Calculations Duplicated Between Python and JavaScript

| Calculation | Python Location | JavaScript Location | Parity Notes |
|---|---|---|---|
| **Decay Kinetics** | `backend/app/services/decay_engine.py` (`calculate_transit_loss`) | `frontend/js/engine.js` (`calculateDecayLoss`) | Identical formula: $Q_{10}$ scaling, vehicle factors, road vibration, exponential decay. |
| **Freight Economics** | `backend/app/services/optimizer.py` (`calculate_freight_cost`) | `frontend/js/engine.js` (`calculateFreight`) | Identical base fares, rate per ton-km, minimum km rate, and highway tolls per vehicle type. |
| **Financial Waterfall** | `backend/app/services/optimizer.py` (`optimize`) | `frontend/js/engine.js` (`optimizeAll`) | Identical gross turnover, handling, APMC cess, and net realization arithmetic. |
| **Route Ranking & Badges** | `backend/app/services/optimizer.py` (`optimize`) | `frontend/js/engine.js` (`optimizeAll`) | Both sort descending by `net_realization` and assign badges (`★ Best Net Realization`, `⚡ Quick Local Sell`, etc.). |
| **Business Insights** | `backend/app/services/optimizer.py` (`optimize`) | `frontend/js/engine.js` (`optimizeAll`) | Identical arbitrage diff against local mandi and heat hazard warnings. |

*Architectural Justification:* The duplicate client engine enables sub-millisecond slider responsiveness and standalone offline operation, while the Python service provides the server-side API contract. However, when the backend is online, the frontend delegates to the backend via `api.js`.

---

## 3. Market-Price Endpoints: Simulated vs. Verified Data

**Verdict: 100% of current market data is SIMULATED.**

- `mandis_db.py`: Baseline prices are hardcoded numbers multiplied by fixed commodity factors (`CROP_PRICE_BENCHMARKS`) and randomized with `random.uniform(-1.5, 1.5)`.
- `/api/market-prices/live`: Synthesizes arbitrary price deltas (`random.uniform(-1.8, 2.2)`) and arrival changes.
- `/api/market-prices/history/{crop_id}`: Synthesizes a fictitious 7-day walk backwards using random floats.
- `app.js` (`startLiveTicker`): Client-side ticker periodically adds `(Math.random() * 2.4 - 1.1)`.
- **Zero records originate from AGMARKNET or Open Government Data Platform India.**

---

## 4. External Dependencies of Existing Endpoints and Schemas

- **Python standard library:** `math`, `random`, `datetime`, `os`, `typing`, `enum`.
- **Third-party Python packages:** `fastapi`, `uvicorn`, `pydantic`.
- **External database:** None (in-memory lists and dictionaries).
- **External web services:** None.

---

## 5. Backend Tests Status

- **Status:** **0 tests exist.**
- No `tests/` directory or `test_*.py` files were present in the repository.

---

## 6. Runtime Environment Status (Windows Host)

- **Python:** Not available in user PATH. The `python.exe` command points to the WindowsApps app execution alias stub. Direct installation via `winget` requires UAC elevation (exit code 50).
- **pip:** Not available in user PATH.
- **Node.js & npm:** Not installed / not available in user PATH.
- **Available tools:** PowerShell 5.1, `curl.exe`, `tar.exe`, `winget.exe`.

---

## 7. Frontend Serving Architecture

- The frontend is served independently by `serve.ps1` on `http://localhost:8080/`.
- It communicates asynchronously via `fetch()` to `http://localhost:8000/` (FastAPI).
- If the backend is unreachable, `api.js` automatically falls back to `ClientAgriEngine` in `engine.js` without crashing or blocking the user.

---

## 8. User Interface Dependencies on Response Fields

The frontend (`frontend/js/api.js` and `frontend/js/app.js`) strictly relies on the following schema fields from `POST /api/routes/optimize`:
- `ranked_routes`:
  - `mandi_id`: string
  - `mandi_name`: string
  - `state`: string
  - `distance_km`: float
  - `transit_hours`: float
  - `unloading_wait_hours`: float
  - `total_duration_hours`: float
  - `price_per_kg`: float
  - `transit_loss_fraction`: float
  - `freshness_index_percent`: float
  - `rank`: int
  - `is_recommended`: bool
  - `recommendation_badge`: string
  - `breakdown`:
    - `saleable_quantity_kg`: float
    - `spoilage_quantity_kg`: float
    - `spoilage_value_loss`: float
    - `gross_revenue`: float
    - `transport_cost`: float
    - `handling_cost`: float
    - `market_cess_cost`: float
    - `holding_cost`: float
    - `total_logistics_cost`: float
    - `net_realization`: float
    - `net_per_kg`: float
- `crop.id`: string
- `quantity_kg`: float
- `vehicle_type`: string
- `ambient_temp_celsius`: float
- `insights`: list of strings

Any extension to the optimizer response must preserve these fields to avoid breaking the dashboard.
