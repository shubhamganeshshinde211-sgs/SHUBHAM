# AgriRoute Intelligence — Team Reproduction & Operational Guide

## 1. Executive Summary & Objective

This document provides complete, deterministic instructions for any team member, auditor, or engineer to set up, execute, test, and verify the **AgriRoute Intelligence** decision-support system.

The system is designed to evaluate multi-mandi agricultural dispatch decisions across 7 APMC markets in Maharashtra and regional corridors, balancing price arbitrage against transport freight, APMC statutory costs, and biological decay kinetics.

---

## 2. Environment Architecture & Prerequisites

### 2.1 Workspace Location
```powershell
C:\Users\VEDANT\.gemini\antigravity-ide\scratch\agriroute-intelligence
```

### 2.2 Python Runtime
- **Python Version**: `Python 3.11.9 (64-bit)`
- **Isolated Virtual Environment**: Located directly in `./.python/` (or activated via standard virtual environment tools).
- **Core Dependencies**:
  - `fastapi >= 0.110.0`
  - `uvicorn >= 0.28.0`
  - `scipy >= 1.13.0` (SciPy HiGHS LP solver for multi-market allocation)
  - `numpy >= 1.26.0`
  - `lightgbm >= 4.3.0` (Gradient-boosted decision trees for price forecasting)
  - `pytest >= 8.1.0`
  - `starlette / httpx`

---

## 3. Quickstart: Launching the System

### Step 1: Activate or Target the Python Environment
Open a PowerShell terminal within the repository root:
```powershell
cd C:\Users\VEDANT\.gemini\antigravity-ide\scratch\agriroute-intelligence
```

Verify the Python executable:
```powershell
.\.python\python.exe --version
# Expected: Python 3.11.9
```

### Step 2: Start the FastAPI Authoritative Backend
Launch the uvicorn application server on localhost port `8000`:
```powershell
.\.python\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
- **Health Check**: `GET http://127.0.0.1:8000/health` (Returns `{"status": "ok", "app": "AgriRoute Intelligence"}`)
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **Interactive OpenAPI Specification**: `http://127.0.0.1:8000/openapi.json`

### Step 3: Start the Web Dashboard
In a separate terminal, launch the static HTTP server on port `8080`:
```powershell
powershell -ExecutionPolicy Bypass -File .\serve.ps1 -Port 8080
```
- Open your browser to `http://localhost:8080` to access the interactive AgriRoute Intelligence Command Center.

---

## 4. Running Automated Tests

The test suite verifies data pipelines, forecasting models, economic invariants, LP allocation constraints, adversarial resilience, and API endpoints.

To run the entire suite (43 passing tests):
```powershell
.\.python\python.exe -m pytest tests/ -v
```

### Test Suite Directory Structure:
| Test File | Verification Purpose | Test Count |
| :--- | :--- | :---: |
| [`tests/test_adversarial_resilience.py`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/tests/test_adversarial_resilience.py) | Edge conditions: price crash, arbitrage traps, fleet sizing, biological expiry, mass conservation | 11 |
| [`tests/test_mathematical_invariants.py`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/tests/test_mathematical_invariants.py) | Monotonicity: freight, spoilage, price, holding; zero double-deduction; LP feasibility | 10 |
| [`tests/test_api_endpoints.py`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/tests/test_api_endpoints.py) | FastAPI routes: `/health`, `/api/routes/optimize`, `/api/forecasts/evaluation`, `/api/forecasts/decision-backtest` | 7 |
| [`tests/test_data_pipeline.py`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/tests/test_data_pipeline.py) | SQLite ingest, date-continuity, schema validation, outlier filtering | 6 |
| [`tests/test_forecasting.py`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/tests/test_forecasting.py) | LightGBM feature engineering, chronological splits, horizon consistency | 5 |
| [`tests/test_economic_optimizer.py`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/tests/test_economic_optimizer.py) | Freight formulas, decay kinetics, unit realization parity | 4 |

---

## 5. Reproducing Economic Decision Backtesting

The Economic Decision Backtester evaluates whether the dispatch optimizer produces mathematically superior financial realization compared to baseline policies over historical data **without future-information leakage**.

### Step 1: Execute the Walk-Forward Decision Backtest
Run the backtest CLI script:
```powershell
.\.python\python.exe -m backend.app.forecasting.decision_backtester
```

### Execution Details:
- **Evaluated Dataset**: 2,275 daily APMC records in `backend/app/data/market_observations.db`.
- **Decision Span**: Chronological rolling window from `2026-08-26` to `2026-10-02` (165 decisions across 5 crops).
- **Leakage Prevention**: At date $t$, the optimizer observes *strictly* $T \le t$. Arrival realization is evaluated at $t + \lceil \text{transit\_hours}/24 \rceil$ using true ground-truth APMC clearing prices observed on that arrival date.
- **Policies Evaluated**:
  1. **Policy A (Local-Only)**: Sells 100% at the closest local mandi (Nashik/Pimpalgaon, 25–40 km).
  2. **Policy B (Highest Observed Price)**: Naive quoted price chasing (sends consignment to mandi with highest headline rate on decision date).
  3. **Policy C (Highest Forecast Price)**: Sends consignment to mandi with highest predicted rate without factoring logistics costs.
  4. **Policy D (Economic Optimizer)**: Solves multi-mandi allocation and route selection maximizing net realization after freight, APMC cess, holding, and biological decay.
  5. **Hindsight Oracle**: Identifies the ex-post optimal dispatch in hindsight (theoretical upper bound).

### Artifacts Produced:
- Machine-Readable: [`backend/app/forecasting/models/decision_backtest_results.json`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/backend/app/forecasting/models/decision_backtest_results.json)
- Human-Readable Audit: [`docs/decision_backtest_report.md`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/docs/decision_backtest_report.md)

---

## 6. Reproducing Price Forecasting Model Evaluation

The forecasting evaluation benchmarks LightGBM against classical baselines (Rolling Average, Seasonal Naive, Last-Observed Persistence) over a rolling-origin walk-forward protocol:

```powershell
.\.python\python.exe -m backend.app.forecasting.backtester
```

### Artifacts Produced:
- Evaluation Metrics: `backend/app/forecasting/models/evaluation_results.json`
- Model Audit Report: `docs/forecast_evaluation_report.md`

---

## 7. Data Provenance & Verification

AgriRoute Intelligence explicitly distinguishes between three tiers of data:

1. **Observed Historical Data (`HISTORICAL_DATA`)**:
   - Location: `backend/app/data/market_observations.db`
   - Schema: SQLite table `market_observations` (date, market_id, commodity_id, modal_price_per_kg, arrival_volume_mt, min_price, max_price).
   - Origin: Official AGMARKNET historical daily arrivals and modal market clearing prices.
2. **Model Forecasts (`FORECAST_DATA`)**:
   - Generated dynamically by `PriceForecastingEngine`.
   - Accompanied by empirical 80% prediction intervals (`[lower_bound, upper_bound]`) and data-staleness flags.
3. **Demo / Fallback Mode (`DEMO_DATA`)**:
   - Enabled only when SQLite database is unpopulated or backend is offline.
   - Distinctly flagged in UI with amber warning pill: `DEMO SIMULATION`.

---

## 8. Common Troubleshooting & FAQs

### Problem 1: `AttributeError: type object 'MultiMandiRouteOptimizer' has no attribute 'optimize_routes'`
- **Cause**: The entry point method is named `optimize(request: OptimizationRequest)` in `MultiMandiRouteOptimizer`.
- **Fix**: Call `MultiMandiRouteOptimizer.optimize(req)`.

### Problem 2: Port Conflict on 8000 or 8080
- **Check active port listener**:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000, 8080 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess
  ```
- **Terminate conflicting process**:
  ```powershell
  Stop-Process -Id <OwningProcessId> -Force
  ```

### Problem 3: Missing SQLite Database
- If `market_observations.db` is missing, rebuild from the data pipeline adapter:
  ```powershell
  .\.python\python.exe -c "from backend.app.data_pipeline.pipeline import MarketDataPipeline; p = MarketDataPipeline(); p.sync_all_sources()"
  ```

---

## 9. Verification Sign-Off Checklist

Before presenting or deploying:
- [x] All 43 pytest unit and resilience tests pass without errors.
- [x] Backend responds to `GET /health` with HTTP 200.
- [x] Backend responds to `GET /api/forecasts/decision-backtest` with HTTP 200.
- [x] Static server serves dashboard at `http://localhost:8080`.
- [x] Mass conservation invariant holds: $Q_{\text{initial}} = Q_{\text{sold}} + Q_{\text{lost}} + Q_{\text{unallocated}}$.
- [x] No credentials or secret keys are stored in source code.
